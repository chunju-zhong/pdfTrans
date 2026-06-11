# Checklist

## 步骤1.5 ThreadPoolExecutor 死锁修复

- [x] 步骤1.5 不再使用 `with ThreadPoolExecutor` 语句
- [x] 正常完成时 `executor.shutdown(wait=True)` 等待线程结束
- [x] 超时时 `executor.shutdown(wait=False)` 不等待线程，避免死锁
- [x] 超时后该页标记为无公式，继续处理下一页
- [x] 超时分支中不再执行无效的 `del formula_detect_pipeline` + `gc.collect()`

## C++ 内存池强制释放

- [x] `_force_release_memory()` 函数已实现，Linux 调用 `malloc_trim(0)`，macOS 调用 `malloc_zone_pressure_relief`
- [x] 步骤1完成后调用 `_force_release_memory()`
- [x] 步骤1.5 每页完成后调用 `_force_release_memory()`
- [x] 步骤2 每页完成后调用 `_force_release_memory()`
- [x] 步骤3 每页完成后调用 `_force_release_memory()`
- [x] `_force_release_memory()` 日志记录释放前后的 RSS 变化

## 步骤3 超时保护

- [x] 步骤3 使用 ThreadPoolExecutor + 超时机制（与修复后的步骤1.5 相同模式）
- [x] 超时后 `shutdown(wait=False)`，该页公式结果为空
- [x] 步骤3 超时不影响其他页面的公式识别

## 主进程批次间内存释放

- [x] 每批次完成后主进程执行 `gc.collect()`
- [x] 批次间有 3 秒等待时间让操作系统回收内存
- [x] 系统可用内存 < 1.5GB 时等待 10 秒并在后续批次设置 skip_formula
- [x] 每批次完成后清理该批次的临时图像文件

## 内存监控日志

- [x] 每批次前后记录主进程 RSS 和系统可用内存
- [x] 记录与前一批次相比的内存变化量

## 端到端验证

- [ ] OCR_BATCH_SIZE=1 时，第二批次公式版面分析不再卡死
- [ ] OCR_BATCH_SIZE=5 时，多批次处理正常完成
- [ ] 步骤1.5 超时场景下，该页被跳过而非整个进程死锁
- [ ] 步骤3 超时场景下，该页公式结果为空而非整个进程卡死
- [ ] 内存使用在步骤间有可见的下降趋势（通过 `_force_release_memory` 日志验证）
