# 修复分批OCR公式版面分析卡死 + 内存优化 Spec

## Why

当 `OCR_BATCH_SIZE=1`（每批仅处理1页）时，第一批次正常完成，但第二批次在步骤1.5（公式版面分析）仍然卡死。深度代码审查发现**卡死的直接原因是 ThreadPoolExecutor 死锁**，同时存在 C++ 内存池不释放和主进程批次间资源未释放等加剧问题。

## 根因分析

### 问题1（直接死因）: ThreadPoolExecutor `with` 语句导致死锁

[步骤1.5代码](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L797-L813)：

```python
with ThreadPoolExecutor(max_workers=1) as executor:       # ← with 语句
    future = executor.submit(_predict_with_pipeline, ...)
    try:
        results = future.result(timeout=120)
    except FuturesTimeoutError:
        del formula_detect_pipeline
        gc.collect()
        continue   # ← 试图跳到下一页，但必须先退出 with 块！
```

**死锁路径**：
1. `future.result(timeout=120)` 超时 → 抛出 `FuturesTimeoutError`
2. `continue` 语句要求退出当前代码块
3. 退出 `with ThreadPoolExecutor` 块时，Python 自动调用 `executor.shutdown(wait=True)`
4. `shutdown(wait=True)` 等待所有已提交任务完成
5. 但 `pipeline.predict()` 卡住了，线程永远不会结束
6. **→ 死锁！进程永远卡在 `shutdown()` 调用上**

这就是为什么即使 batch_size=1（只有1页），第二批次仍然卡死——**第一批次的步骤1.5 如果超时，整个子进程就死锁了**，外层心跳超时才会杀掉它，但第二批次启动时系统内存已被压缩。

### 问题2: PaddlePaddle C++ 内存池不归还操作系统

PaddlePaddle 使用 C++ 层内存池管理张量内存。`del pipeline` + `gc.collect()` 只释放 Python 引用，C++ 内存池保留在进程 RSS 中不归还 OS。

**影响**：步骤1完成后 ~1.4GB RSS 未释放，步骤1.5 创建新管线时内存叠加，16GB 系统上可能触发大量 swap。

### 问题3: 主进程批次间资源未释放

[pdf_extractor.py 批处理循环](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py#L258-L289)：
- `all_results` 累积 `PdfExtraction` 对象
- `temp_images_dir` 所有批次完成后才清理
- 主进程未在批次间执行 `gc.collect()`
- 子进程退出后 OS 需要时间回收内存，但主进程立即启动下一个子进程

### 问题4: 步骤3 缺少超时保护

步骤3 与步骤1.5 使用相同的 `use_formula=True` 管线，但没有超时保护。某页卡住只能靠外层心跳超时终止整个子进程。

## 为什么不用子进程隔离步骤1.5/3？

使用 `multiprocessing.Process` 替代线程来隔离每页公式检测**理论可行但代价过高**：
- 每页需重新加载 PaddlePaddle 模型（~1.4GB），模型加载耗时 10-30 秒
- 对于 10 页 PDF，步骤1.5 就需要 10 次模型加载，总耗时增加 100-300 秒
- 进程创建/销毁开销 + 进程间通信序列化开销

**更好的方案**：修复 ThreadPoolExecutor 死锁 + 添加 `malloc_trim` 释放 C++ 内存。子线程超时后无法被强制终止，但我们可以：
1. 不用 `with` 语句，改用 `shutdown(wait=False)` 避免死锁
2. 超时后跳过该页，残留线程在进程退出时自动清理
3. 用 `malloc_trim` 确保步骤间 C++ 内存归还 OS

## What Changes

- 修复步骤1.5 的 ThreadPoolExecutor 死锁：不用 `with` 语句，超时后 `shutdown(wait=False)`
- 在子进程内步骤间添加 `malloc_trim` 强制归还 C++ 内存池给操作系统
- 为步骤3 添加与步骤1.5 相同的线程级超时保护
- 在主进程批次间添加显式内存释放和间隔等待
- 添加批次间内存监控日志

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`、`modules/pdf_extractor.py`
- Affected specs: `optimize-ocr-memory`、`intel-mac-16gb-ocr-mem`、`ocr-three-layer-protection-and-batching`

## ADDED Requirements

### Requirement: 修复步骤1.5 ThreadPoolExecutor 死锁

系统 SHALL 修复步骤1.5 的 ThreadPoolExecutor 死锁问题。不再使用 `with` 语句管理 ThreadPoolExecutor，改为手动管理生命周期，超时后调用 `shutdown(wait=False)` 避免阻塞。

#### Scenario: 公式检测正常完成

- **WHEN** 某页公式检测在超时时间内完成
- **THEN** 正常获取结果，调用 `executor.shutdown(wait=True)` 等待线程结束
- **AND** 继续处理结果

#### Scenario: 公式检测超时

- **WHEN** 某页公式检测超过 `FORMULA_DETECT_PAGE_TIMEOUT`（120秒）
- **THEN** 调用 `executor.shutdown(wait=False)` 不等待线程结束
- **AND** 该页标记为无公式，继续处理下一页
- **AND** 残留线程在进程退出时自动清理

#### Scenario: 公式检测抛出异常

- **WHEN** 公式检测线程抛出非超时异常
- **THEN** 记录错误日志，该页标记为无公式
- **AND** 继续处理下一页

### Requirement: 子进程内步骤间强制释放 C++ 内存池

系统 SHALL 在每个步骤完成后（`del pipeline` + `gc.collect()` 之后），调用 `malloc_trim(0)` 强制将空闲的 C++ 堆内存归还给操作系统。

- Linux: 调用 `ctypes.CDLL("libc.so.6").malloc_trim(0)`
- macOS: 调用 `ctypes.CDLL("libc.dylib").malloc_trim(0)`（macOS 的 malloc 基于 jemalloc，`malloc_trim` 可能不可用；备选方案为 `ctypes.CDLL("libc.dylib").malloc_zone_pressure_relief(0, 0)`）

#### Scenario: 步骤1完成后释放内存

- **WHEN** 步骤1完成，执行 `del layout_pipeline` + `gc.collect()`
- **THEN** 额外调用 `malloc_trim(0)` 或等效机制
- **AND** RSS 内存显著下降（预期从 ~1400MB 降至 ~200-400MB）

#### Scenario: 步骤1.5 每页完成后释放内存

- **WHEN** 步骤1.5 某页公式检测完成，执行 `del formula_detect_pipeline` + `gc.collect()`
- **THEN** 额外调用 `malloc_trim(0)` 或等效机制

#### Scenario: 步骤2/3 每页完成后释放内存

- **WHEN** 步骤2 或步骤3 某页处理完成
- **THEN** 额外调用 `malloc_trim(0)` 或等效机制

### Requirement: 步骤3 添加线程级超时保护

系统 SHALL 为步骤3（公式识别）添加与步骤1.5 相同的线程级超时保护机制。使用 ThreadPoolExecutor（不用 `with` 语句）+ `shutdown(wait=False)` 模式。

#### Scenario: 公式识别正常完成

- **WHEN** 某页公式识别在超时时间内完成
- **THEN** 正常获取公式识别结果

#### Scenario: 公式识别超时

- **WHEN** 某页公式识别超过超时时间
- **THEN** 调用 `shutdown(wait=False)`，该页公式结果为空
- **AND** 继续处理下一页

### Requirement: 主进程批次间内存释放

系统 SHALL 在每个批次完成后，在主进程中执行以下操作：
1. 显式调用 `gc.collect()` 释放 Python 对象
2. 记录主进程和系统可用内存
3. 等待短暂间隔（3秒），让操作系统回收前一批次子进程的物理内存
4. 检查系统可用内存是否足够启动下一批次

#### Scenario: 批次间内存释放

- **WHEN** 第 N 批次 OCR 子进程完成
- **THEN** 主进程执行 `gc.collect()`
- **AND** 记录当前主进程 RSS 和系统可用内存
- **AND** 等待 3 秒让操作系统回收内存

#### Scenario: 系统内存极度不足

- **WHEN** 批次间检查发现系统可用内存 < 1.5GB
- **THEN** 等待 10 秒让操作系统完成内存回收
- **AND** 再次检查，仍不足则在后续批次的 ocr_params 中设置 skip_formula=True
- **AND** 记录警告日志

### Requirement: 批次间内存监控日志

系统 SHALL 在批次处理循环中添加详细的内存监控日志。

#### Scenario: 批次处理内存日志

- **WHEN** 批次处理循环运行
- **THEN** 每批次前后记录主进程 RSS 和系统可用内存
- **AND** 记录与前一批次相比的内存变化量
- **AND** 日志格式为 "批次N: 主进程RSS=XXX MB, 系统可用=XXX GB, 变化=+/-XXX MB"

## MODIFIED Requirements

### Requirement: 步骤1.5 超时处理逻辑

原步骤1.5 使用 `with ThreadPoolExecutor` + `FuturesTimeoutError` 处理超时，存在死锁。修改为手动管理 ThreadPoolExecutor 生命周期，超时后 `shutdown(wait=False)` 避免死锁。

### Requirement: 批次间 temp_images_dir 清理

原 `temp_images_dir` 在所有批次完成后才清理。修改为每批次完成后清理该批次的临时图像文件，减少磁盘占用和文件缓存压力。

## REMOVED Requirements

无
