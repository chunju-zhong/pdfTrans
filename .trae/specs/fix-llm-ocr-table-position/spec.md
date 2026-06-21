# 修复 LLM OCR 表格位置固定不随原 PDF 位置 Spec

## Why
LLM OCR 模式下，表格始终绘制在固定位置（y=100pt 起始），而非原始 PDF 中的实际位置。根因：DeepSeek-OCR `<|ref|>` 标签中的 `<|det|>` 表格坐标被代码丢弃，转而使用硬编码估算位置。

## What Changes
- 在 `_parse_ref_tags_response` 中，当 `<|ref|>` 块包含 HTML 表格时，保留其 `<|det|>` 坐标作为表格 bbox，而非丢弃后重新估算
- 修改 `_extract_tables_from_text`，接受外部传入的 `table_bbox_map` 参数，优先使用 LLM 返回的坐标
- 多表格场景下，基于文本块上下文位置推算各表格 y 坐标，避免叠放

## Impact
- Affected code: [llm_extractor.py](modules/ocr/llm_extractor.py) `_parse_ref_tags_response`、`_extract_tables_from_text`
- Affected specs: fix-llm-ocr-table-rendering, fix-llm-ocr-bbox-accuracy

## ADDED Requirements

### Requirement: DeepSeek-OCR ref 标签中保留表格 bbox
`_parse_ref_tags_response` 处理 `<|ref|>` 块时，若文本包含 HTML 表格，SHALL 保留其 `<|det|>` 坐标作为表格 bbox。

#### Scenario: ref 标签包含表格和 det 坐标
- **WHEN** `<|ref|>` 块的文本包含 `<table>` 且有有效的 `<|det|>` 坐标
- **THEN** 使用该 det 坐标（归一化 → PDF 点）作为表格 bbox，而非硬编码估算

#### Scenario: ref 标签包含表格但无 det 坐标
- **WHEN** `<|ref|>` 块的文本包含 `<table>` 但无有效 det 坐标
- **THEN** 回退到估算位置

### Requirement: 多表格垂直偏移
同一页有多个表格时，SHALL 避免所有表格叠放在同一 y 坐标。

#### Scenario: 同一页多个表格
- **WHEN** 同一页有 2 个以上表格且无精确 bbox
- **THEN** 每个后续表格的 y 坐标基于前一个表格的高度向下偏移

## MODIFIED Requirements

### Requirement: _extract_tables_from_text 接受外部 bbox
`_extract_tables_from_text` SHALL 接受 `table_bbox_map` 参数，允许调用方提供从 LLM 响应中提取的坐标。当 `table_bbox_map` 中有对应表格的 bbox 时，优先使用。
