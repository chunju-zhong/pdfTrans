# 修复 LLM OCR 文本块字体大小为0导致PDF不可见 Spec

## Why
LLM OCR 提取的 TextBlock 没有字体样式信息（font_size=0.0），PDF 生成器使用 0.0 字体大小渲染导致 "float division by zero" 错误，文本以 0pt 字体渲染，完全不可见。

## What Changes
- 在 PDF 生成器中，当 `original_font_size == 0` 时，根据 bbox 尺寸估算合理的字体大小
- 估算公式：`font_size = bbox_height * 0.75`（与 PaddleOCR 回退逻辑一致）

## Impact
- Affected code: `modules/pdf_generator.py`

## MODIFIED Requirements

### Requirement: 字体大小为0时自动估算
当 TextBlock 的 `font_size == 0` 时，PDF 生成器 SHALL 根据 bbox 高度估算合理的字体大小。

#### Scenario: LLM OCR 文本块字体大小估算
- **WHEN** TextBlock 的 `font_size == 0` 且 `bbox_height > 0`
- **THEN** 估算 `font_size = bbox_height * 0.75`，上限 36pt

#### Scenario: bbox 也为0
- **WHEN** TextBlock 的 `font_size == 0` 且 `bbox_height == 0`
- **THEN** 使用默认字体大小 12pt
