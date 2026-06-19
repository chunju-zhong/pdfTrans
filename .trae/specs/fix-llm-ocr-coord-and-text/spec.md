# 修复 LLM OCR 坐标转换及文本提取完整性 Spec

## Why

LLM OCR 提取器返回的 bbox 坐标是图像像素坐标，未转换为 PDF 点坐标，导致翻译文本位置偏移严重。同时，DeepSeek-OCR 返回的文本包含 Markdown 标题前缀（`#`、`##`），未清理导致翻译内容异常。此外，title/sub_title 类型文本块仍被标记为非正文，未参与翻译。

## What Changes

- LLM OCR 提取器在解析响应后，将像素坐标转换为 PDF 点坐标（参照 PaddleOCR 的 `_pixel_to_pdf_coords` 方法）
- `_parse_ref_tags_response` 方法清理 Markdown 标题前缀（`#`、`##`、`###`）
- 验证并确保 LLM OCR 所有文本块的 `is_body_text=True` 生效

## Impact

- Affected code: `modules/ocr/llm_extractor.py`
- Affected specs: `fix-llm-ocr-title-untranslated`

## ADDED Requirements

### Requirement: LLM OCR 像素坐标转 PDF 点坐标

LLM OCR 提取器 SHALL 将 DeepSeek-OCR 返回的像素坐标转换为 PDF 点坐标，使用页面尺寸和图像尺寸计算缩放比例。

#### Scenario: 单页坐标转换

- **WHEN** 页面宽度为 720pt，图像宽度为 1500px，DeepSeek-OCR 返回 bbox (56, 93, 562, 141)
- **THEN** 转换后 bbox 为 (56 * 720/1500, 93 * 720/1500, 562 * 720/1500, 141 * 720/1500) ≈ (26.88, 44.64, 269.76, 67.68)

#### Scenario: 图像块坐标转换

- **WHEN** 图像块 bbox 为像素坐标
- **THEN** 同样需要转换为 PDF 点坐标

### Requirement: 清理 Markdown 标题前缀

`_parse_ref_tags_response` 方法 SHALL 清理 DeepSeek-OCR 返回文本中的 Markdown 标题前缀（`#`、`##`、`###` 等），仅保留实际文本内容。

#### Scenario: 标题文本清理

- **WHEN** DeepSeek-OCR 返回 `# Removal of the primary depends on the raw water characteristics`
- **THEN** TextBlock.text 为 `Removal of the primary depends on the raw water characteristics`

#### Scenario: 副标题文本清理

- **WHEN** DeepSeek-OCR 返回 `## Lesson:`
- **THEN** TextBlock.text 为 `Lesson:`

## MODIFIED Requirements

### Requirement: LLM OCR 所有文本块都需翻译

LLM OCR 模式下，翻译服务 SHALL 翻译所有文本块，包括 title/sub_title 等非正文块。`is_body_text` 必须在提取阶段设置为 `True`，且不被后续流程覆盖。

#### Scenario: LLM OCR 标题翻译

- **WHEN** LLM OCR 提取的文本块类型为 title 或 sub_title
- **THEN** 该文本块的 `is_body_text=True`，且被翻译服务翻译
