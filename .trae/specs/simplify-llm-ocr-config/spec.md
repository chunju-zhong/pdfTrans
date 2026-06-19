# LLM OCR 复用翻译引擎配置 Spec

## Why
LLM OCR 的 API 提供商（AIPing/SiliconFlow）与翻译引擎完全相同，当前单独列出 `--ocr-llm-provider` 参数和 Web 界面的提供商选择是多余的。用户选择翻译引擎后，LLM OCR 应自动复用同一套 API 配置，无需额外选择。

## What Changes
- 移除 `--ocr-llm-provider` CLI 参数
- 移除 Web 界面的 LLM 提供商下拉框
- 移除 `OCR_LLM_PROVIDER`、`OCR_LLM_MODEL_AIPING`、`OCR_LLM_MODEL_SILICON_FLOW` 配置项
- 新增 `OCR_LLM_MODEL` 统一配置项（默认 `'Qwen/Qwen3-VL-8B'`）
- `LlmOcrExtractor` 接收 `translator_type` 参数（`'aiping'` 或 `'silicon_flow'`），自动复用对应翻译引擎的 API Key/URL
- 整条调用链传递 `translator_type` 给 LLM OCR：CLI/Web → TranslationService → PdfExtractor → LlmOcrExtractor

## Impact
- Affected specs: 无
- Affected code: `modules/ocr/llm_extractor.py`, `config.py`, `cli.py`, `cli/translate_command.py`, `app.py`, `templates/index.html`, `static/js/main.js`, `modules/pdf_extractor.py`, `services/translation_service.py`, `modules/ocr/factory.py`, `tests/test_llm_ocr.py`

## MODIFIED Requirements

### Requirement: LLM OCR API 配置
LLM OCR SHALL 复用当前翻译引擎（`translator_type`）的 API Key 和 API URL，不再需要单独的 provider 参数。

#### Scenario: 使用 AIPing 翻译 + LLM OCR
- **WHEN** 用户选择翻译引擎为 `aiping`，启用 OCR 模式且引擎为 `llm`
- **THEN** LLM OCR 使用 `config.AIPING_API_KEY` 和 `config.AIPING_API_URL`，模型为 `config.OCR_LLM_MODEL`

#### Scenario: 使用 SiliconFlow 翻译 + LLM OCR
- **WHEN** 用户选择翻译引擎为 `silicon_flow`，启用 OCR 模式且引擎为 `llm`
- **THEN** LLM OCR 使用 `config.SILICON_FLOW_API_KEY` 和 `config.SILICON_FLOW_API_URL`，模型为 `config.OCR_LLM_MODEL`

### Requirement: CLI 参数简化
CLI SHALL 移除 `--ocr-llm-provider` 参数，LLM OCR 的提供商由翻译引擎自动决定。

#### Scenario: CLI 使用 LLM OCR
- **WHEN** 用户执行 `python cli.py translate input.pdf --ocr --ocr-engine llm --translator aiping --source en --target zh`
- **THEN** LLM OCR 自动使用 AIPing 的 API 配置

### Requirement: Web 界面简化
Web 界面 SHALL 移除 LLM 提供商下拉框，LLM OCR 的提供商由翻译引擎选择自动决定。

#### Scenario: Web 选择 LLM OCR
- **WHEN** 用户勾选"启用OCR提取"并选择"LLM OCR"引擎
- **THEN** 不显示 LLM 提供商选择，LLM OCR 自动使用当前翻译引擎的 API 配置

## REMOVED Requirements
### Requirement: 独立 LLM OCR 提供商配置
**Reason**: LLM OCR 与翻译使用同一平台（AIPing/SiliconFlow），独立配置增加用户认知负担且无实际价值
**Migration**: 移除 `OCR_LLM_PROVIDER`、`OCR_LLM_MODEL_AIPING`、`OCR_LLM_MODEL_SILICON_FLOW`，替换为 `OCR_LLM_MODEL`；`LlmOcrExtractor` 构造函数参数从 `provider` 改为 `translator_type`
