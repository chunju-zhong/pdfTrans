# Tasks

- [x] Task 1: 在 `_extract_page` 中精细化异常处理，区分超时错误并提供中文可读消息
  - [x] SubTask 1.1: 在 `try` 块中增加对 `openai.APITimeoutError` 的单独捕获，生成中文可读错误消息包含超时时间、页码和模型名
  - [x] SubTask 1.2: 其他异常保持原有格式不变
  - [x] SubTask 1.3: 返回值从 `None` 改为携带错误信息的结构化结果（如 `(None, error_msg)`），供上层使用

- [x] Task 2: 在 `_extract_page` 中添加超时重试机制
  - [x] SubTask 2.1: 在捕获 `APITimeoutError` 后，最多重试 1 次
  - [x] SubTask 2.2: 重试前记录警告日志 "第 N 页首次请求超时，正在进行第 1 次重试"
  - [x] SubTask 2.3: 重试仍然超时时记录错误日志并返回空结果+错误消息

- [x] Task 3: 在 `extract_from_pdf` 中传播超时错误
  - [x] SubTask 3.1: 接收 `_extract_page` 返回的错误消息，存入局部列表
  - [x] SubTask 3.2: 提取完成后，若有超时错误，通过 `progress_callback('page_error', ...)` 传递
  - [x] SubTask 3.3: 适配返回值变化（`_extract_page` 返回 `(result, error_msg)`）

- [x] Task 4: 在 `translation_service` 中根据具体错误原因生成消息
  - [x] SubTask 4.1: 在 `extract_pdf_content` 中，当提取结果为空时，检查是否有从 OCR 传递来的具体错误原因
  - [x] SubTask 4.2: 若有超时错误，调用 `task.set_error("OCR 提取失败：API 请求超时，请检查网络连接或 API 服务状态")` 并终止流程
  - [x] SubTask 4.3: 若无错误记录，保持现有 "没有找到需要翻译的文本块" 行为不变

# Task Dependencies
- Task 2 依赖 Task 1（重试机制需要先有超时区分）
- Task 3 依赖 Task 1（错误传播需要 Task 1 的结构化错误返回）
- Task 4 依赖 Task 3（需要 Task 3 传递的错误信息）
