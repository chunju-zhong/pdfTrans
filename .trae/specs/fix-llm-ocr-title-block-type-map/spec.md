# 修复 LLM OCR 标题类型文本块未翻译 Spec

## Why
LLM OCR 模式下，`BLOCK_TYPE_MAP` 将 `title`、`sub_title`、`section_title` 映射为 `is_body_text=False`，翻译服务只翻译 `is_body_text=True` 的块，导致所有标题类型文本块被跳过，输出 PDF 中标题保持原文未翻译。

之前的 `fix-llm-ocr-title-untranslated` spec 声称已修复此问题，但实际未修改 `BLOCK_TYPE_MAP` 中的映射，根因仍然存在。

## What Changes
- 将 `BLOCK_TYPE_MAP` 中 `title`、`sub_title`、`section_title` 的 `is_body_text` 改为 `True`
- 这些类型的 `block_type_int` 保持不变（仍为 1，表示标题），仅影响是否参与翻译

## Impact
- Affected code: `modules/ocr/llm_extractor.py`（`BLOCK_TYPE_MAP` 常量）
- Affected specs: `fix-llm-ocr-title-untranslated`（原修复不完整，本次补全）

## MODIFIED Requirements

### Requirement: LLM OCR 标题类型文本块参与翻译
LLM OCR 模式下，`title`、`sub_title`、`section_title` 类型的文本块 SHALL 被标记为 `is_body_text=True`，确保翻译服务将其纳入翻译流程。

#### Scenario: LLM OCR 标题翻译
- **WHEN** LLM OCR 提取的文本块类型为 `title`、`sub_title` 或 `section_title`
- **THEN** 该文本块的 `is_body_text` 为 `True`，会被翻译

#### Scenario: 页眉页脚仍不翻译
- **WHEN** LLM OCR 提取的文本块类型为 `header`、`footer`、`page_number` 或 `footnote`
- **THEN** 该文本块的 `is_body_text` 为 `False`，不会被翻译

#### Scenario: 标题类型标识不变
- **WHEN** LLM OCR 提取的文本块类型为 `title`、`sub_title` 或 `section_title`
- **THEN** 该文本块的 `block_type` 仍为 1（标题类型），用于 PDF 生成时区分样式
