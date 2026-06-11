# Tasks

- [x] Task 1: 修复步骤1.5 ThreadPoolExecutor 死锁
  - [x] SubTask 1.1: 将 `with ThreadPoolExecutor(max_workers=1) as executor:` 改为手动创建 `executor = ThreadPoolExecutor(max_workers=1)`
  - [x] SubTask 1.2: 正常完成时调用 `executor.shutdown(wait=True)` 等待线程结束
  - [x] SubTask 1.3: 超时时调用 `executor.shutdown(wait=False)` 不等待线程，避免死锁
  - [x] SubTask 1.4: 移除超时分支中的 `del formula_detect_pipeline` + `gc.collect()`（线程仍持有引用，del 无效）
  - [x] SubTask 1.5: 确保超时后 `continue` 不会触发 `shutdown(wait=True)`

- [x] Task 2: 添加 `_force_release_memory()` 工具方法
  - [x] SubTask 2.1: 在 `PaddleOcrExtractor` 中添加 `_force_release_memory()` 静态方法，Linux 调用 `ctypes.CDLL("libc.so.6").malloc_trim(0)`，macOS 调用 `ctypes.CDLL("libc.dylib").malloc_zone_pressure_relief(0, 0)`
  - [x] SubTask 2.2: 在方法中记录释放前后的 RSS 变化日志
  - [x] SubTask 2.3: 在步骤1完成后（`del layout_pipeline` + `gc.collect()` 之后）调用 `_force_release_memory()`
  - [x] SubTask 2.4: 在步骤1.5 每页完成后调用 `_force_release_memory()`
  - [x] SubTask 2.5: 在步骤2 每页完成后调用 `_force_release_memory()`
  - [x] SubTask 2.6: 在步骤3 每页完成后调用 `_force_release_memory()`

- [x] Task 3: 为步骤3 添加线程级超时保护
  - [x] SubTask 3.1: 将步骤3 的 `pipeline.predict()` 调用包装在 ThreadPoolExecutor + 超时机制中（与修复后的步骤1.5 相同模式）
  - [x] SubTask 3.2: 超时后调用 `shutdown(wait=False)`，该页公式结果为空
  - [x] SubTask 3.3: 添加超时日志和进度回调

- [x] Task 4: 主进程批次间内存释放
  - [x] SubTask 4.1: 在 `pdf_extractor.py` 的批次循环中，每批次完成后添加 `gc.collect()`
  - [x] SubTask 4.2: 添加批次间等待（3秒），让操作系统回收前一批次子进程的物理内存
  - [x] SubTask 4.3: 添加系统可用内存检查，不足 1.5GB 时等待 10 秒并在后续批次设置 skip_formula
  - [x] SubTask 4.4: 每批次完成后清理该批次的临时图像文件（`ocr_page_{page_num}.png`）

- [x] Task 5: 批次间内存监控日志
  - [x] SubTask 5.1: 在 `pdf_extractor.py` 的批次循环中，每批次前后记录主进程 RSS 和系统可用内存
  - [x] SubTask 5.2: 计算并记录与前一批次相比的内存变化量

# Task Dependencies

- [Task 1] 是最关键的修复，独立于其他 Task
- [Task 2] 独立于 Task 1，可并行开发
- [Task 3] 依赖 [Task 1] 的模式（复用相同的 ThreadPoolExecutor 修复模式）
- [Task 4] 独立于 Task 1-3，可并行开发
- [Task 5] 可与 Task 1-4 并行开发
