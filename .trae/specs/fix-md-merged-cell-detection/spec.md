# 修复合并单元格 span 检测失败（data 中有 None 但 rows_data 无 None）Spec

## Why

Markdown 表格合并单元格检测失败。`_convert_table_to_markdown()` 检测 `row_span > 1` 或 `col_span > 1`，但 `PdfCell` 的 `row_span`/`col_span` 始终为默认值1。

**根因**：`compute_span_from_none_positions` 基于 `rows_data`（PyMuPDF 原始 bbox 矩阵）计算 span，但 PyMuPDF 对某些合并单元格表格返回均匀网格（每行每列都有 bbox），导致 `bbox_matrix` 中没有 `None`，`span_map` 为空。而 `data`（字符分配后的文本矩阵）中有 `None` 位置——因为合并单元格的字符被分配到了起始单元格，被合并位置没有字符。

## What Changes

- 在 `table_processor.py` 中，当 `span_map` 为空但 `data` 中存在 `None` 时，基于 `data` 的 `None` 分布重新计算 `span_map`

## Impact

- **PDF**：正向影响——之前这类表格也没有合并效果（网格线穿过合并区域），补充 span 后 PDF 也会正确渲染合并单元格
- **Word**：正向影响——补充 span 后 Word 也会正确调用 `cell.merge()`
- **Markdown**：正向影响——补充 span 后 Markdown 会使用 HTML 格式输出合并单元格
- Affected code: `modules/extractors/table_processor.py` 的表格构建逻辑

## ADDED Requirements

### Requirement: 基于 data 的 None 分布补充 span 检测

当 `span_map`（基于 `rows_data` 计算）为空但 `data` 中存在 `None` 时，SHALL 基于 `data` 的 `None` 分布重新计算 `span_map`。

#### Scenario: PyMuPDF 返回均匀网格但 data 有 None

- **WHEN** `rows_data` 中所有位置都有 bbox（无 None），但 `data` 中某些位置为 None
- **THEN** 基于 `data` 的 None 分布构建虚拟 bbox 矩阵，调用 `compute_span_from_none_positions` 计算 span
- **AND** 将计算结果设置到对应 `PdfCell` 的 `row_span`/`col_span`
- **AND** 被合并位置在 `cell_matrix` 中设为 `None`

#### Scenario: rows_data 已有 None（PyMuPDF 检测到合并）

- **WHEN** `rows_data` 中已有 None 位置
- **THEN** 行为不变，使用 `rows_data` 的 `span_map`

## MODIFIED Requirements

无

## REMOVED Requirements

无
