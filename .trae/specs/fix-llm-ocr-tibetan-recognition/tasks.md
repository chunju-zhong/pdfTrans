# Tasks

- [x] Task 1: 在 LlmOcrExtractor 构造函数中新增 `source_lang` 参数并存储
  - [x] 1.1: 修改 `__init__` 方法签名，新增 `source_lang='en'` 参数
  - [x] 1.2: 存储 `self.source_lang = source_lang`
- [x] Task 2: 修改 DeepSeek-OCR prompt，注入源语言信息
  - [x] 2.1: 当 `source_lang` 为藏文（`bo`）时，在 prompt 中添加藏文识别提示
  - [x] 2.2: 对其他语言，在 prompt 中添加语言提示
- [x] Task 3: 修改通用 VLM prompt，注入源语言信息
  - [x] 3.1: 在 `VLM_JSON_SYSTEM_PROMPT` 的 user 消息中添加源语言提示
  - [x] 3.2: 对藏文等低资源语言添加特别强调（逐字提取、不要翻译）
- [x] Task 4: 修改 PdfExtractor 传递 source_lang 到 LlmOcrExtractor
  - [x] 4.1: 在 `PdfExtractor` 的 OCR 初始化处传递 `source_lang`
- [x] Task 5: 修改 translation_service 传递 source_lang 到 PdfExtractor
  - [x] 5.1: 在调用 `extract_pdf_content` 或创建 `PdfExtractor` 时传递 `source_lang`

# Task Dependencies
- Task 2, 3 依赖 Task 1
- Task 4 依赖 Task 1
- Task 5 依赖 Task 4
