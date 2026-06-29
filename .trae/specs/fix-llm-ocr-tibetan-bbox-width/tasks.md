# Tasks

- [x] Task 1: VLM prompt 注入 `source_lang` 支持藏文特殊引导
  - [x] 1.1: 在 `_extract_page` 中，当 `source_lang == 'bo'` 时，在 VLM user message 中添加藏文 OCR 引导文本
  - [x] 1.2: 引导文本强调"每个文本块的 bbox 必须覆盖从最左字符到最右字符的完整行宽"
  - [x] 1.3: 引导文本强调"不要因音节分隔符「་」或音节间空格而拆分一行文本"
  - [x] 1.4: 非藏文语言时 prompt 行为不变

- [x] Task 2: 废弃 `fix-pixel-to-pdf-y-flip` spec
  - [x] 2.1: 在 `fix-pixel-to-pdf-y-flip/spec.md` 中添加废弃说明
  - [x] 2.2: 确认 `_pixel_to_pdf_coords` 中不存在 Y 轴翻转代码

# Task Dependencies

- Task 1 和 Task 2 独立（可并行执行）
