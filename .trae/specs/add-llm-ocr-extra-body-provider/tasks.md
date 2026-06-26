# Tasks

- [x] Task 1: 在 config.py 中新增 OCR_LLM_EXTRA_BODY 配置项
  - [x] 1.1: 从环境变量 `OCR_LLM_EXTRA_BODY` 读取 JSON 字符串，解析为 dict，解析失败时默认为 None
- [x] Task 2: 在 LlmOcrExtractor._extract_page 的 API 调用中传递 extra_body
  - [x] 2.1: 当 config.OCR_LLM_EXTRA_BODY 不为 None 时，在 `client.chat.completions.create()` 调用中添加 `extra_body` 参数

# Task Dependencies
- Task 2 依赖 Task 1
