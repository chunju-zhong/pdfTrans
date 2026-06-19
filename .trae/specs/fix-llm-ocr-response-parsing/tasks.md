# Tasks

- [x] Task 1: 修改 `_extract_page()` 的 prompt 格式，适配 DeepSeek-OCR
  - [x] 将自定义中文 prompt 改为 DeepSeek-OCR 原生格式：`<image>\n<|grounding|>Convert the document to markdown.`
  - [x] 添加原始响应日志（`result_text[:500]`）
  - [x] JSON 解析失败时也记录原始响应

- [x] Task 2: 修改 `_parse_response()` 支持 DeepSeek-OCR 的 Markdown 输出
  - [x] 保留现有 JSON 解析作为第一优先级
  - [x] 新增 Markdown 解析：按段落分割（`\n\n`），映射为 TextBlock
  - [x] 新增 `<|ref|>...<|/ref|>` 标签解析：提取标签内文本映射为 TextBlock
  - [x] 解析优先级：JSON → `<|ref|>` 标签 → Markdown 段落

- [x] Task 3: 更新测试
  - [x] 添加 Markdown 格式响应的解析测试
  - [x] 添加 `<|ref|>` 标签响应的解析测试
  - [x] 运行全部测试验证无回归

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
