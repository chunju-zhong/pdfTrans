# Tasks

- [x] Task 1: 新增停滞检测（stall detection）
  - [x] SubTask 1.1: 在 `_run_ocr_once` 中新增 `last_progress_time` 和 `last_pages_done` 变量，收到 STEP_PROGRESS 且 pages_done 增加时更新 `last_progress_time`
  - [x] SubTask 1.2: 在主循环中增加停滞检测：如果 `time.time() - last_progress_time > stall_timeout`（默认 1800 秒），终止子进程并抛出 OcrRetryableError
  - [x] SubTask 1.3: `_run_ocr_once` 函数签名新增 `stall_timeout` 参数，默认 1800 秒
  - [x] SubTask 1.4: `run_ocr_in_subprocess` 中从 config 读取 `OCR_STALL_TIMEOUT`，传入 `_run_ocr_once`

- [x] Task 2: 放宽 max_total_time 为兜底安全网
  - [x] SubTask 2.1: 将 config.py 中 `OCR_MAX_TOTAL_TIME` 从 7200 改为 86400（24 小时）
  - [x] SubTask 2.2: 在 `run_ocr_in_subprocess` 中，降级后的 `max_total_time` 不再被 `config_max_total_time` 截断（移除 `min(degraded_timeout, config_max_total_time)` 中的截断逻辑，改为仅对初始值截断）

- [x] Task 3: 实现分批 OCR 处理
  - [x] SubTask 3.1: 在 config.py 中新增 `OCR_BATCH_SIZE = 5`（可配置）配置项
  - [x] SubTask 3.2: 在 `pdf_extractor.py` 的 `extract` 方法中，当页数超过 `OCR_BATCH_SIZE` 时，将页面分成多批，每批调用 `run_ocr_in_subprocess`
  - [x] SubTask 3.3: 实现分批结果合并逻辑：将每批的 text_blocks、tables、formula_blocks、image_regions 合并为完整结果
  - [x] SubTask 3.4: 分批处理时通过日志报告总体进度（当前批次/总批数）
  - [x] SubTask 3.5: 某批失败时，该批独立重试，不影响其他批次；所有批次完成后，失败的批次使用空结果

# Task Dependencies
- Task 1 和 Task 2 可并行
- Task 3 独立于 Task 1/2，可并行
