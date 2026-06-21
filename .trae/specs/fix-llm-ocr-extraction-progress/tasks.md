# Tasks

- [x] Task 1: 为 `LlmOcrExtractor.extract_from_pdf` 添加 progress_callback 参数和调用
  - [x] 方法签名新增 `progress_callback=None` 参数
  - [x] 逐页循环开始前发送 `step_start` 回调（step=1, step_name='LLM OCR提取'）
  - [x] 每完成一页后发送 `step_progress` 回调（pages_done, total_pages）
  - [x] 所有页面完成后发送 `step_complete` 回调

- [x] Task 2: `PdfExtractor.extract` 中 LLM OCR 分支传递 progress_callback
  - [x] 将 `progress_callback=progress_callback` 传入 `extractor.extract_from_pdf()`

# Task Dependencies
- [Task 2] depends on [Task 1]
