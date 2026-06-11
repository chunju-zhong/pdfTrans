# Tasks

- [x] Task 1: 移除 `_force_release_memory` 方法及调用
  - [x] 删除 `PaddleExtractor._force_release_memory()` 方法定义（paddle_extractor.py L154-L176）
  - [x] 删除步骤1中两处 `self._force_release_memory()` 调用（paddle_extractor.py L1174, L1184）
  - [x] 保留 `del pipeline` + `gc.collect()` 不变

- [x] Task 2: 移除分批 OCR 处理逻辑
  - [x] 将 pdf_extractor.py 中 OCR 模式的分支简化：移除 `batch_size` 判断和分批循环，统一为单次 `run_ocr_in_subprocess()` 调用
  - [x] 移除分批相关的进度回调构造（`_make_batch_callback`）
  - [x] 移除批次间内存监控日志（`_batch_rss_before`、`_batch_avail_before`、`_delta` 等）
  - [x] 移除批次间 `gc.collect()`、`time.sleep(3)` 和临时图像清理循环
  - [x] 移除 `_merge_batch_results()` 调用，直接使用子进程返回结果

- [x] Task 3: 移除 `_merge_batch_results` 辅助函数
  - [x] 删除 pdf_extractor.py 中的 `_merge_batch_results` 函数定义（L22-L71）

- [x] Task 4: 移除 `OCR_BATCH_SIZE` 配置项
  - [x] 删除 config.py 中的 `OCR_BATCH_SIZE` 行（L101）

- [x] Task 5: 清理无用 import
  - [x] 移除 pdf_extractor.py 中不再使用的 `time`、`gc`、`psutil` import
  - [x] 清理 translation_service.py 中 batch_idx/total_batches 相关死代码

# Task Dependencies
- Task 2 依赖 Task 3（先移除 `_merge_batch_results` 再简化调用逻辑）
- Task 5 依赖 Task 1-4 完成后检查
