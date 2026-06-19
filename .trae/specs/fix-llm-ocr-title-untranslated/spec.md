# 修复 LLM OCR 标题/副标题未翻译及字体大小估算不准 Spec

## Why
LLM OCR 提取的文本块中，title/sub_title 类型被标记为 `is_body_text=False`，翻译服务只翻译正文块，导致标题和副标题完全未被翻译。同时，字体大小估算 `bbox_height * 0.75` 对大 bbox 直接命中 36pt 上限，导致字体过大溢出。

## What Changes
- LLM OCR 模式下，所有文本块（包括 title/sub_title）都应被翻译
- 字体大小估算改为基于行数：`font_size = bbox_height / estimated_lines * 0.75`

## Impact
- Affected code: `services/translation_service.py`, `modules/ocr/llm_extractor.py`

## MODIFIED Requirements

### Requirement: LLM OCR 所有文本块都需翻译
LLM OCR 模式下，翻译服务 SHALL 翻译所有文本块，包括 title/sub_title 等非正文块。

#### Scenario: LLM OCR 标题翻译
- **WHEN** LLM OCR 提取的文本块 `is_body_text=False`（如 title/sub_title）
- **THEN** 该文本块仍应被翻译

#### Scenario: 非 OCR 模式不变
- **WHEN** 非 OCR 模式（文本型 PDF）
- **THEN** 仅翻译正文块（行为不变）

### Requirement: LLM OCR 字体大小估算考虑行数
LLM OCR 文本块的字体大小估算 SHALL 考虑文本行数，避免大 bbox 直接命中上限。

#### Scenario: 多行文本块
- **WHEN** bbox 高度为 133px，文本有 3 行
- **THEN** 估算字体大小 = 133 / 3 * 0.75 ≈ 33pt（而非直接 36pt 上限）
