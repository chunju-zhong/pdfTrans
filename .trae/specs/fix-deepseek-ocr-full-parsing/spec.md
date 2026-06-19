# 修复 DeepSeek-OCR 响应解析：提取实际文本和坐标 Spec

## Why
当前 `<|ref|>` 标签解析只提取了类型标签（title/text/image），而非实际文本内容。DeepSeek-OCR 的完整格式是 `<|ref|>type<|/ref|><|det|>[[bbox]]<|/det|>\nactual_text`，需要同时提取类型、坐标和实际文本。

## What Changes
- 修改 `_parse_ref_tags_response()` 解析完整的 DeepSeek-OCR 响应格式
- 从 `<|ref|>` 提取类型标签（title/text/image/sub_title 等）
- 从 `<|det|>` 提取 bbox 坐标
- 提取 `<|det|>` 后的实际文本内容
- 根据类型标签设置 `is_body_text`（title/sub_title 为 False）

## Impact
- Affected code: `modules/ocr/llm_extractor.py`

## MODIFIED Requirements

### Requirement: DeepSeek-OCR 完整响应解析
LLM OCR SHALL 正确解析 DeepSeek-OCR 的完整响应格式。

#### Scenario: 完整格式解析
- **WHEN** DeepSeek-OCR 返回 `<|ref|>title<|/ref|><|det|>[[54, 23, 940, 87]]<|/det|>\n# Removal of the primary...`
- **THEN** TextBlock.text = "# Removal of the primary...", bbox = (54, 23, 940, 87), is_body_text = False

#### Scenario: 类型标签映射
- **WHEN** `<|ref|>` 标签为 title 或 sub_title
- **THEN** `is_body_text = False`
- **WHEN** `<|ref|>` 标签为 text
- **THEN** `is_body_text = True`

#### Scenario: image 类型处理
- **WHEN** `<|ref|>` 标签为 image
- **THEN** 创建 PdfImage 而非 TextBlock，bbox 从 `<|det|>` 提取
