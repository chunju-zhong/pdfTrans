# Word 和 Markdown 表格合并单元格优化 Spec

## Why

PDF 输出已完整支持合并单元格（row_span/col_span），但 Word 和 Markdown 输出完全忽略了合并信息，将合并单元格展开为普通网格+空单元格，导致：
1. **Word**：合并单元格显示为多个独立格子，原始合并位置是空白格，视觉上完全丢失合并效果
2. **Markdown**：合并单元格的文本只出现在起始列，后续列显示空值，表格结构被破坏

## What Changes

- Word 生成器使用 python-docx 的 `cell.merge()` API 实现合并单元格
- Markdown 生成器对合并单元格使用 HTML `<td colspan/rowspan>` 标记替代管道表格

## Impact

- Affected code: `modules/docx_generator.py` 的 `_add_table()`、`modules/markdown_generator.py` 的 `_convert_table_to_markdown()`
- 数据模型 `PdfCell.row_span`/`col_span` 已存在，无需修改

## ADDED Requirements

### Requirement: Word 表格支持合并单元格

`_add_table()` SHALL 读取 `PdfCell` 的 `row_span`/`col_span`，使用 python-docx 的 `cell.merge()` 实现合并。

#### Scenario: 单元格跨多列（col_span > 1）

- **WHEN** 单元格 (0,1) 的 `col_span=3`
- **THEN** Word 表格中 `word_table.cell(0,1).merge(word_table.cell(0,3))` 被调用
- **AND** 合并后的单元格显示原始文本
- **AND** 被合并位置 (0,2)、(0,3) 不再显示为独立空格

#### Scenario: 单元格跨多行（row_span > 1）

- **WHEN** 单元格 (1,0) 的 `row_span=2`
- **THEN** Word 表格中 `word_table.cell(1,0).merge(word_table.cell(2,0))` 被调用
- **AND** 合并后的单元格显示原始文本

#### Scenario: 普通单元格（row_span=1, col_span=1）

- **WHEN** 单元格无合并属性
- **THEN** 行为与当前一致，正常写入文本

#### Scenario: 被合并位置（cell is None）

- **WHEN** 遍历到 `cell is None` 的位置
- **THEN** 跳过该位置的文本写入（由 merge 操作自动处理）

### Requirement: Markdown 表格支持合并单元格

`_convert_table_to_markdown()` SHALL 检测合并单元格，当存在合并时使用 HTML 表格替代管道表格。

#### Scenario: 表格无合并单元格

- **WHEN** 所有单元格的 `row_span=1, col_span=1`
- **THEN** 使用当前管道表格格式，行为不变

#### Scenario: 表格有合并单元格

- **WHEN** 存在 `row_span > 1` 或 `col_span > 1` 的单元格
- **THEN** 使用 HTML `<table>` 标记生成表格
- **AND** 合并单元格使用 `<td colspan="N" rowspan="M">` 属性
- **AND** 被合并位置（`cell is None`）不生成 `<td>` 标签

#### Scenario: HTML 表格格式

- **WHEN** 使用 HTML 表格格式
- **THEN** 输出格式为：
  ```html
  <table>
    <tr><td>普通</td><td colspan="2">跨列</td></tr>
    <tr><td rowspan="2">跨行</td><td>普通</td><td>普通</td></tr>
    <tr><td>普通</td><td>普通</td></tr>
  </table>
  ```

## MODIFIED Requirements

无

## REMOVED Requirements

无
