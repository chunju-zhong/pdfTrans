# Tasks

- [x] Task 1: LLM OCR 模式下所有文本块都参与翻译
  - [x] 在 `llm_extractor.py` 中，LLM OCR 的所有文本块都设置 `is_body_text=True`

- [x] Task 2: 改进 LLM OCR 字体大小估算，考虑文本行数
  - [x] 在 `llm_extractor.py` 的 `_parse_ref_tags_response` 中，根据文本行数估算 font_size
  - [x] 在 `_parse_json_response` 中同样估算 font_size

# Task Dependencies
- 无
