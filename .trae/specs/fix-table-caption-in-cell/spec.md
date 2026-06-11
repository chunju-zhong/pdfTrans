# 修复表格标题/脚注被合并进单元格 Spec

## Why

非OCR模式下，PyMuPDF 的 `table.rows` 返回的最后一行单元格 bbox 本身就覆盖了表格下方的标题/脚注区域，导致 "Table 5. An example of role prompting" 等标题文本被错误地合并进 `Output` 单元格。当前 `extract_table_cells_by_bbox` 使用 50% 面积重叠判断也无法排除这些字符，因为它们确实落在单元格 bbox 内。

## What Changes

- 保留 `extract_table_cells_by_bbox`（真实 bbox 对非标题行仍有价值，且 `use-real-cell-bbox-non-ocr` 依赖它）
- 新增 `separate_table_caption_and_footnote` 后处理函数，在 `extract_table_cells_by_bbox` 之后对单元格文本做正则匹配，分离标题/脚注
- 分离出的文本作为独立 TextBlock 参与翻译
- `extract_tables_by_pymupdf` 返回值扩展为四元组

## Impact

- Affected specs: `use-real-cell-bbox-non-ocr`（保留其真实 bbox 逻辑，在其之后增加后处理）
- Affected code: `modules/extractors/table_processor.py`、`modules/pdf_extractor.py`

## ADDED Requirements

### Requirement: 表格单元格文本后处理——分离表格标题和脚注

系统在非OCR模式下提取表格后，SHALL 对单元格文本进行后处理，检测并分离表格标题和脚注文本。

#### Scenario: 最后一行单元格包含表格标题

- **WHEN** 最后一行单元格文本中包含匹配 "Table/Figure X." 模式的文本
- **THEN** 系统将该匹配的标题文本从单元格中分离出来
- **AND** 分离出的标题文本作为独立的 TextBlock 返回
- **AND** 单元格中仅保留实际的表格数据文本

#### Scenario: 最后一行单元格包含表格标题后的段落文本

- **WHEN** 表格标题文本之后还有额外的段落文本（如 "The above example shows..."）
- **THEN** 系统将这些段落文本也从单元格中分离出来
- **AND** 分离出的段落文本作为独立的 TextBlock 返回

#### Scenario: 单元格文本全部为标题/脚注

- **WHEN** 分离标题和脚注后，某行单元格的所有文本都被分离
- **THEN** 该行从表格中移除，表格行数相应减少

#### Scenario: 单元格文本不包含标题/脚注

- **WHEN** 单元格文本不包含 "Table/Figure X." 模式
- **THEN** 保持原始行为，不做任何修改

### Requirement: 分离的表格标题/脚注文本作为独立 TextBlock 参与翻译

系统 SHALL 将从表格单元格中分离出的标题/脚注文本作为独立的 TextBlock 返回。

#### Scenario: 表格标题 TextBlock

- **WHEN** 从表格单元格中分离出 "Table X. ..." 格式的标题文本
- **THEN** 创建一个 TextBlock 对象，bbox 位于表格 bbox 下方紧邻位置
- **AND** 该 TextBlock 被加入文本块列表参与翻译

## MODIFIED Requirements

### Requirement: extract_tables_by_pymupdf 返回值扩展

返回值从三元组扩展为四元组：

```python
return pdf_tables, page_tables, page_table_cells, separated_text_blocks
```

其中 `separated_text_blocks` 是一个列表，每个元素是包含 `page_num`, `text`, `bbox` 等信息的字典。

### Requirement: pdf_extractor.py 集成分离的文本块

`pdf_extractor.py` 中：
1. 接收 `separated_text_blocks` 参数
2. 将分离出的文本块转换为 TextBlock 对象，加入 text_blocks 列表
3. 文本块排除逻辑继续使用 `page_table_cells`

## REMOVED Requirements

无
