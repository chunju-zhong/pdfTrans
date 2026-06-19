# Tasks

- [x] Task 1: 简化 config.py — 移除独立 LLM OCR 提供商配置
  - [x] 移除 `OCR_LLM_PROVIDER`、`OCR_LLM_MODEL_AIPING`、`OCR_LLM_MODEL_SILICON_FLOW`
  - [x] 新增 `OCR_LLM_MODEL`（默认 `'Qwen/Qwen3-VL-8B'`）

- [x] Task 2: 修改 LlmOcrExtractor — 用 `translator_type` 替代 `provider`
  - [x] 构造函数参数从 `provider` 改为 `translator_type`
  - [x] `client` 属性根据 `translator_type` 复用翻译引擎的 API Key/URL
  - [x] 模型统一使用 `config.OCR_LLM_MODEL`

- [x] Task 3: 更新工厂函数 — 传递 `translator_type`
  - [x] `create_ocr_extractor('llm', translator_type=...)` 正确传递

- [x] Task 4: 修改 PdfExtractor — 用 `translator_type` 替代 `ocr_llm_provider`
  - [x] 移除 `ocr_llm_provider` 参数
  - [x] OCR 模式创建 LLM 提取器时传入 `self.translator_type`

- [x] Task 5: 修改 TranslationService — 传递 `translator_type` 给 PdfExtractor
  - [x] `extract_pdf_content()` 创建 PdfExtractor 时不再传 `ocr_llm_provider`，改传 `translator_type`
  - [x] 移除 `extract_pdf_content()`、`process_translation()`、`process_translation_sync()` 中的 `ocr_llm_provider` 参数

- [x] Task 6: 简化 CLI — 移除 `--ocr-llm-provider`
  - [x] 删除 `--ocr-llm-provider` 参数定义
  - [x] 删除 translate_command.py 中的 provider 相关日志和传参

- [x] Task 7: 简化 Web 界面 — 移除 LLM 提供商下拉框
  - [x] `app.py` 移除 `ocr_llm_provider` 读取和传参
  - [x] `templates/index.html` 移除 `llm_provider_group` HTML
  - [x] `static/js/main.js` 移除 LLM 提供商联动逻辑

- [x] Task 8: 更新测试
  - [x] 修改 `tests/test_llm_ocr.py` 适配新接口（`translator_type` 替代 `provider`）
  - [x] 移除 `OCR_LLM_PROVIDER` 相关测试
  - [x] 运行全部测试验证无回归
