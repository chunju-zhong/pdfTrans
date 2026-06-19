# Tasks

- [x] Task 1: 修改 `pdf_extractor.py` OCR 模式分支，LLM OCR 直接调用不走子进程
  - [ ] 在 `if self.ocr_mode:` 分支内，根据 `self.ocr_engine` 区分 PaddleOCR 和 LLM OCR
  - [ ] `ocr_engine == 'llm'` 时：通过 `factory.create_ocr_extractor('llm', translator_type=self.translator_type)` 创建提取器，直接调用 `extract_from_pdf()`
  - [ ] `ocr_engine == 'paddle'` 或默认时：保持现有 `run_ocr_in_subprocess()` 调用不变

# Task Dependencies
- 无外部依赖
