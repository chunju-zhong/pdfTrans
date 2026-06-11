# Docx 表格尺寸参照原文 PDF 表格 Spec

## Why

生成 Word 文档中的表格时，`_add_table()` 方法仅使用 `doc.add_table(rows, cols)` 创建表格，完全忽略了原始 PDF 表格的列宽、行高和整体宽度信息，导致 Word 表格各列等宽分布，与原文表格的列宽比例不一致，视觉还原度差。

## What Changes

- `_add_table()` 使用 `PdfTable.col_widths` 设置 Word 表格各列宽度（按比例映射到 Word 可用宽度）
- `_add_table()` 使用 `PdfTable.bbox` 计算表格整体宽度
- `_add_table()` 使用 `PdfTable.row_heights` 设置 Word 表格各行高度
- 当 `col_widths`/`row_heights` 为空时，使用单元格 `width`/`height` 作为 fallback

## Impact

- Affected code: `modules/docx_generator.py` 的 `_add_table()` 方法
- 数据模型 `PdfTable.col_widths`/`row_heights`/`bbox` 和 `PdfCell.width`/`height` 已存在，无需修改

## ADDED Requirements

### Requirement: Word 表格列宽参照原文 PDF 表格

`_add_table()` SHALL 根据 `PdfTable.col_widths` 按比例设置 Word 表格各列宽度，使列宽比例与原文 PDF 表格一致。

#### Scenario: col_widths 可用

- **WHEN** `table.col_widths` 非空且长度等于列数
- **THEN** 计算每列占总宽度的比例
- **AND** 将比例映射到 Word 页面可用宽度（6.5 英寸），设置各列宽度
- **AND** 列宽比例与原文 PDF 表格一致

#### Scenario: col_widths 不可用，但单元格 width 可用

- **WHEN** `table.col_widths` 为空
- **THEN** 从每列非 None 单元格的 `width` 属性中取最大值作为该列宽度
- **AND** 按比例映射到 Word 页面可用宽度

#### Scenario: 两者均不可用

- **WHEN** `table.col_widths` 为空且单元格 `width` 均为 0
- **THEN** 使用 Word 默认等宽分布，行为与当前一致

### Requirement: Word 表格行高参照原文 PDF 表格

`_add_table()` SHALL 根据 `PdfTable.row_heights` 设置 Word 表格各行高度。

#### Scenario: row_heights 可用

- **WHEN** `table.row_heights` 非空且长度等于行数
- **THEN** 将 PDF 点单位行高转换为 Word 的 Emu 单位（1 PDF 点 = 12700 Emu）
- **AND** 设置各行的最小行高

#### Scenario: row_heights 不可用

- **WHEN** `table.row_heights` 为空
- **THEN** 使用单元格 `height` 属性作为 fallback
- **AND** 若均不可用，使用 Word 默认行高

### Requirement: Word 表格整体宽度参照原文 PDF 表格

`_add_table()` SHALL 根据 `PdfTable.bbox` 设置表格整体宽度。

#### Scenario: bbox 可用

- **WHEN** `table.bbox` 非空且有效
- **THEN** 计算 bbox 宽度（PDF 点），转换为英寸（1 点 = 1/72 英寸）
- **AND** 限制最大宽度为 Word 页面可用宽度（6.5 英寸）
- **AND** 设置表格 `autofit = False` 以固定宽度

#### Scenario: bbox 不可用

- **WHEN** `table.bbox` 为空
- **THEN** 使用 Word 默认页面可用宽度

## MODIFIED Requirements

无

## REMOVED Requirements

无
