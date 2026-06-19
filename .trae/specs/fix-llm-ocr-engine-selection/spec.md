# 修复 LLM OCR 引擎选择无效 Spec

## Why
选择 LLM OCR 引擎时，系统仍然使用 PaddleOCR 提取。原因是 `pdf_extractor.py` 中 OCR 模式统一调用 `run_ocr_in_subprocess()`，而该函数硬编码使用 `PaddleOcrExtractor`，完全忽略 `ocr_engine` 参数。

## What Changes
- `pdf_extractor.py` 中 OCR 模式分支：当 `ocr_engine == 'llm'` 时，直接调用 `LlmOcrExtractor`，不走子进程隔离
- `run_ocr_in_subprocess()` 仅用于 PaddleOCR（子进程隔离是为 PaddleOCR 内存管理设计的，LLM OCR 是 API 调用无需隔离）

## Impact
- Affected code: `modules/pdf_extractor.py`
- Affected specs: `simplify-llm-ocr-config`

## MODIFIED Requirements

### Requirement: OCR 引擎选择生效
当用户选择 `--ocr-engine llm` 时，系统 SHALL 使用 `LlmOcrExtractor` 提取内容，而非 PaddleOCR。

#### Scenario: 选择 LLM OCR 引擎
- **WHEN** 用户启用 OCR 模式且 `ocr_engine == 'llm'`
- **THEN** 系统使用 `LlmOcrExtractor`（通过 `factory.create_ocr_extractor('llm', translator_type=...)` 创建），不走子进程隔离

#### Scenario: 选择 PaddleOCR 引擎（默认）
- **WHEN** 用户启用 OCR 模式且 `ocr_engine == 'paddle'` 或未指定
- **THEN** 系统使用 `run_ocr_in_subprocess()` 调用 PaddleOCR（行为不变）
