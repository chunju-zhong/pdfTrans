# Tasks

- [x] Task 1: 修复 _ocr_progress_cb 逻辑（translation_service.py）
  - [x] SubTask 1.1: 将 STEP_WEIGHTS 从 `{1: 0.45, 1.5: 0.05, 2: 0.25, 3: 0.25}` 改为 `{1: 0.80, 2: 0.20}`
  - [x] SubTask 1.2: 在 step_complete 处理中，计算当前步骤的累积权重上限并设为 ocr_progress（例如步骤 1 完成时 ocr_progress=0.80，步骤 2 完成时 ocr_progress=1.00）
  - [x] SubTask 1.3: 移除步骤 1.5 的跳过警告处理代码
  - [x] SubTask 1.4: 保留 batch_idx/total_batches 处理不变

- [x] Task 2: 在 extract_from_pdf 中添加步骤 2 回调（paddle_extractor.py）
  - [x] SubTask 2.1: 在步骤 2 图像裁剪循环前添加 step_start 回调
  - [x] SubTask 2.2: 在步骤 2 图像裁剪循环后添加 step_complete 回调

# Task Dependencies
- Task 1 和 Task 2 可并行
