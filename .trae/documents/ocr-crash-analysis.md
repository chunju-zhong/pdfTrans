# OCR 运行时进程崩溃问题分析与修复计划

## 问题摘要

OCR 功能运行时，Flask 进程在 PP-StructureV3 初始化后静默崩溃退出，伴随 `resource_tracker` 信号量泄漏警告。

## 当前状态分析

### 错误日志时间线

```
18:31:24.926 - 初始化OCR提取器: engine=paddleocr, lang=en
18:31:24.950 - 开始OCR提取PDF, 共4页
18:31:25.873 - 初始化PP-StructureV3管线: lang=en, device=cpu
18:31:25 ~ 18:31:50 - 只有 /progress 轮询请求，无OCR处理日志
18:31:50+ - 进程崩溃退出
resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown
```

**关键观察**：PP-StructureV3 初始化后，没有任何 OCR 处理结果日志，进程直接挂掉。`resource_tracker` 的信号量泄漏是进程异常退出的**症状**而非根因。

### 根因分析

经过代码审查，识别出 **3 个相互关联的问题**：

#### P0: Flask DEBUG 模式导致 reloader fork 与 PaddleOCR 冲突

**证据**：
- [config.py:13](file:///Users/chunju/work/pdfTrans/config.py#L13) — `DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'`，默认 `True`
- [app.py:20](file:///Users/chunju/work/pdfTrans/app.py#L20) — `app.config.from_object(config)` 将 DEBUG=True 加载到 Flask 配置
- [app.py:326](file:///Users/chunju/work/pdfTrans/app.py#L326) — `app.run(host='0.0.0.0', port=port)` 未显式禁用 reloader

**机制**：Flask DEBUG=True 时，Werkzeug reloader 通过 `os.fork()` 创建子进程监控文件变化。PaddleOCR/PPStructureV3 内部使用 `multiprocessing` 模块（数据加载器、Semaphore、Queue 等 IPC 原语），这些资源在 fork 后状态不一致：
- 信号量计数值被复制但等待队列不正确
- 已获取的信号量在子进程中永远无法释放
- 共享内存段引用计数错误

**结果**：子进程中的 PaddleOCR 管线在首次推理时触发内存访问错误，进程崩溃。

#### P0: PP-StructureV3 非线程安全，被多线程并发调用

**证据**：
- [app.py:94](file:///Users/chunju/work/pdfTrans/app.py#L94) — 每次翻译请求在新 `threading.Thread` 中执行
- [paddle_extractor.py:98](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L98) — `self._pipeline` 是普通实例变量，非 `threading.local()`
- [paddle_extractor.py:257](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L257) — `self.pipeline.predict()` 无线程保护

**机制**：`PPStructureV3.predict()` 内部维护推理上下文和内存池，不是线程安全的。如果两个 OCR 请求并发执行，共享同一个 pipeline 实例会导致 C++ 底层 segfault。

#### P1: 延迟初始化存在竞态条件

**证据**：
- [paddle_extractor.py:125](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L125) — `if self._pipeline is None:` 无锁保护
- [pdf_extractor.py](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py) — `ocr_extractor` 属性同理无锁

**机制**：两个线程同时首次访问 OCR，可能同时创建两个 `PPStructureV3` 实例，导致 GPU/CPU 内存重复分配或第二个实例覆盖第一个。

### 信号量泄漏解释

`resource_tracker` 报告的 `leaked semaphore objects` 是 PaddleOCR 内部 `multiprocessing` 原语在进程异常退出时未被正确清理的结果。这不是独立问题，而是进程崩溃的附带症状。

## 修复方案

### 修改 1: 禁用 Flask reloader（解决 P0 fork 问题）

**文件**: [app.py](file:///Users/chunju/work/pdfTrans/app.py#L326)

**修改**: `app.run()` 显式禁用 reloader，或根据 OCR 模式动态禁用

```python
# 方案 A：始终禁用 reloader（推荐，生产环境不需要）
app.run(host='0.0.0.0', port=port, use_reloader=False)

# 方案 B：仅在 OCR 模式下禁用
app.run(host='0.0.0.0', port=port, use_reloader=not config.USE_OCR)
```

**理由**：Flask reloader 仅用于开发调试，与 PaddleOCR 的 multiprocessing 机制根本不兼容。生产环境不应使用 reloader。

### 修改 2: PaddleOCR 管线改为线程本地存储（解决 P0 线程安全问题）

**文件**: [paddle_extractor.py](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py)

**修改**: 将 `self._pipeline` 改为 `threading.local()` 存储，每个线程拥有独立的 pipeline 实例

```python
import threading

class PaddleOcrExtractor(OcrExtractor):
    def __init__(self, ...):
        self._local = threading.local()

    @property
    def pipeline(self):
        if not hasattr(self._local, 'pipeline') or self._local.pipeline is None:
            # ... 初始化逻辑 ...
            self._local.pipeline = PPStructureV3(...)
        return self._local.pipeline
```

**理由**：`PPStructureV3.predict()` 不是线程安全的，每个线程需要独立实例。代价是内存占用增加（每个线程一个模型实例），但避免了 segfault。

**替代方案**：如果内存是瓶颈，可使用 `threading.Lock` 串行化 `predict()` 调用，但会降低并发性能。

### 修改 3: 延迟初始化加锁（解决 P1 竞态条件）

**文件**: [paddle_extractor.py](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py)

**修改**: 为 pipeline 初始化添加 double-check locking

```python
_init_lock = threading.Lock()

@property
def pipeline(self):
    if not hasattr(self._local, 'pipeline') or self._local.pipeline is None:
        with self._init_lock:
            if not hasattr(self._local, 'pipeline') or self._local.pipeline is None:
                self._local.pipeline = PPStructureV3(...)
    return self._local.pipeline
```

### 修改 4: config.py DEBUG 默认值调整

**文件**: [config.py](file:///Users/chunju/work/pdfTrans/config.py#L13)

**修改**: 将 DEBUG 默认值改为 `False`

```python
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
```

**理由**：生产环境不应默认开启 DEBUG 模式，且 DEBUG 模式与 PaddleOCR 不兼容。

## 假设与决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| reloader 处理方式 | 完全禁用 | reloader 与 PaddleOCR multiprocessing 不兼容，生产环境不需要 |
| 线程安全策略 | threading.local | 比 Lock 串行化更安全，避免死锁风险 |
| DEBUG 默认值 | False | 生产环境标准做法，且避免 reloader 问题 |

## 验证步骤

1. 启动 Flask 应用（确认 DEBUG=False, use_reloader=False）
2. 上传扫描版 PDF，启用 OCR 模式
3. 验证 OCR 处理正常完成，无进程崩溃
4. 同时发起两个 OCR 请求，验证无 segfault
5. 确认进程退出时无 `resource_tracker` 信号量泄漏警告
6. 检查 `app.log` 中 PP-StructureV3 初始化和 OCR 处理日志完整
