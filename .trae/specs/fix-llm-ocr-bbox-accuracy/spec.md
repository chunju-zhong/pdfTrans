# 修复 LLM OCR bbox 不准确导致渲染位置错误 Spec

## Why

DeepSeek-OCR 模型返回的 bbox 坐标与原始 PDF 中的实际文本位置存在系统性偏移。例如，"Lesson:" 的 OCR bbox 为 (336.0, 202.5)，但原始 PDF 中实际位置为 (505.3, 169.2)，偏差达 169pt。这导致：
1. redaction 遮盖了错误区域，原文未被遮盖
2. 翻译文本被放置在错误位置
3. 窄 bbox（如 "Lesson:" 仅 36.48pt 宽）无法容纳翻译文本

## What Changes

- 在 `pdf_generator.py` 中，对 LLM OCR 提取的文本块，使用 PyMuPDF 的 `page.search_for()` 在原始 PDF 中搜索原始文本，获取实际位置
- 使用搜索到的实际位置替换 OCR bbox，用于 redaction 和文本渲染
- 当搜索失败时（文本被修改或找不到），回退到 OCR bbox

## Impact

- Affected code: `modules/pdf_generator.py`
- Affected specs: `fix-llm-ocr-font-size-and-rendering`（redaction padding 调整仍保留）

## ADDED Requirements

### Requirement: LLM OCR 文本块使用原始 PDF 实际位置

PDF 生成器 SHALL 对 LLM OCR 提取的文本块，在原始 PDF 页面中搜索原始文本的实际位置，用于 redaction 和文本渲染。

搜索流程：
1. 在 `_draw_translated_text` 的 redaction 阶段，对每个文本块，使用 `page.search_for(original_text, quads=False)` 搜索原始文本
2. 如果搜索到结果，计算所有匹配区域的并集矩形作为实际 bbox
3. 使用实际 bbox 替换 OCR bbox，用于 redaction 和文本渲染
4. 如果搜索失败（返回空列表），回退到 OCR bbox

#### Scenario: "Lesson:" 文本块位置修正

- **WHEN** LLM OCR 返回 "Lesson:" 的 bbox=(336.0, 202.5, 372.5, 221.2)，但原始 PDF 中 "Lesson:" 位于 (505.3, 169.2, 559.8, 187.2)
- **THEN** 使用 `page.search_for("Lesson:")` 找到实际位置 (505.3, 169.2, 559.8, 187.2)
- **AND** redaction 使用实际位置 (505.3-h_padding, 169.2-v_padding, 559.8+h_padding, 187.2+v_padding)
- **AND** 翻译文本 "课程：" 渲染在实际位置 (505.3, 169.2, 559.8, 187.2)

#### Scenario: 标题文本位置修正

- **WHEN** LLM OCR 返回标题 bbox=(25.9, 12.0, 452.2, 42.2)，但原始 PDF 中标题文本 "Removal of the primary depends on the raw water characteristics" 跨越更宽的区域
- **THEN** 使用 `page.search_for("Removal")` 等搜索找到实际位置
- **AND** redaction 覆盖完整的标题区域，包括 "water characteristics"

#### Scenario: 搜索失败时回退

- **WHEN** `page.search_for(original_text)` 返回空列表（文本可能被 OCR 修改或不存在）
- **THEN** 回退使用 OCR bbox 进行 redaction 和文本渲染

### Requirement: 传递原始文本到 PDF 生成器

LLM OCR 提取的 TextBlock SHALL 保留原始文本（翻译前），以便 PDF 生成器使用原始文本在 PDF 中搜索实际位置。

- 在 TextBlock 模型中添加 `original_text` 属性，存储翻译前的文本
- 在翻译服务中，翻译完成后将原始文本保存到 `original_text`
- 在 PDF 生成器中，使用 `original_text` 搜索实际位置

#### Scenario: TextBlock 保留原始文本

- **WHEN** 翻译服务处理 LLM OCR 文本块 "Lesson:" → "课程："
- **THEN** TextBlock.block_text = "课程："，TextBlock.original_text = "Lesson:"

## MODIFIED Requirements

### Requirement: LLM OCR 字体大小估算（原 fix-llm-ocr-font-size-and-rendering）

当使用原始 PDF 实际位置替换 OCR bbox 后，字体大小估算 SHALL 使用实际 bbox 重新计算。

- 在 PDF 生成器中，如果搜索到实际位置，使用实际 bbox 的宽度和高度重新估算 font_size
- 重新估算公式与 llm_extractor.py 相同：`min(bbox_height * 0.75, 36)`
- 不再使用面积法（因为实际 bbox 更准确，行数法足够）
