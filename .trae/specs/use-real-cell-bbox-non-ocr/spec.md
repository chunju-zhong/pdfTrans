# 非 OCR 模式表格精准还原 Spec

## Why

非 OCR 模式下，`extract_table_cells_by_bbox` 已经从 PyMuPDF 的 `table.rows[i].cells[j]` 获取了真实的单元格 bbox（包含合并单元格的跨行跨列信息），但在 `extract_tables_by_pymupdf` 中，这些真实 bbox 被完全丢弃，改用 `calculate_cell_bbox` 做均匀分割。这导致：

1. **合并单元格丢失**：均匀分割无法表达跨行跨列的单元格，合并单元格被拆成多个独立小格
2. **行列尺寸不准**：`calculate_cell_bbox` 假设所有行等高、所有列等宽，但真实表格行高列宽各不相同
3. **绘制偏差**：`pdf_generator.py` 使用均匀分割的 cell bbox 绘制，无法精准还原原表格结构

## What Changes

- 在 `extract_tables_by_pymupdf` 中，使用 `extract_table_cells_by_bbox` 返回的真实单元格 bbox 替代 `calculate_cell_bbox` 的均匀分割
- 从真实单元格 bbox 推算 `row_heights` 和 `col_widths`，而非从均匀分割的 cell 尺寸计算
- `pdf_generator.py` 的 `_draw_translated_table` 已支持使用 cell.bbox 绘制（第 538 行），无需修改绘制逻辑

## Impact

- Affected specs: `refactor-table-to-grid-layout`（OCR 模式的网格布局，不影响）
- Affected code: `modules/extractors/table_processor.py`（`extract_tables_by_pymupdf`）、`modules/extractors/coordinate_utils.py`（新增从真实 bbox 推算行列尺寸的函数）

## ADDED Requirements

### Requirement: 使用 PyMuPDF 真实单元格 bbox

系统在非 OCR 模式提取表格时，SHALL 使用 PyMuPDF 提供的真实单元格 bbox，而非均匀分割计算。

#### Scenario: extract_table_cells_by_bbox 成功返回真实 bbox

- **WHEN** `extract_table_cells_by_bbox` 成功返回 `data` 和 `cell_bboxes`
- **AND** `cell_bboxes` 不为空
- **THEN** 使用 `rows_data`（包含真实 bbox 的行×列矩阵）构建 PdfCell，而非调用 `calculate_cell_bbox`
- **AND** 每个单元格的 bbox 直接使用 PyMuPDF 提供的真实坐标

#### Scenario: extract_table_cells_by_bbox 失败或返回空 bbox

- **WHEN** `extract_table_cells_by_bbox` 失败或返回空的 `cell_bboxes`
- **THEN** 回退到 `calculate_cell_bbox` 均匀分割（保持现有行为）

### Requirement: 从真实单元格 bbox 推算 row_heights 和 col_widths

系统 SHALL 从真实单元格 bbox 推算每行的行高和每列的列宽，而非从均匀分割的 cell 尺寸计算。

#### Scenario: 推算行高

- **WHEN** 所有单元格 bbox 可用
- **THEN** 第 i 行的行高 = 该行所有单元格中最大的 (y1 - y0)
- **AND** 同行单元格共享相同的 y0 和 y1（PyMuPDF 保证）

#### Scenario: 推算列宽

- **WHEN** 所有单元格 bbox 可用
- **THEN** 第 j 列的列宽 = 该列所有单元格中最大的 (x1 - x0)
- **AND** 对于合并单元格（跨多列），其宽度应按比例分配到所跨的列

#### Scenario: 合并单元格的列宽分配

- **WHEN** 某单元格跨 N 列（x1 - x0 覆盖多列）
- **THEN** 该单元格的宽度按 N 等分分配到所跨的各列
- **AND** 非合并单元格的宽度直接作为所在列的宽度
- **AND** 每列最终宽度取所有贡献值中的最大值

### Requirement: PdfCell 保留合并单元格的完整 bbox

对于合并单元格，PdfCell 的 bbox SHALL 保留其完整的跨行跨列区域，不拆分。

#### Scenario: 合并单元格绘制

- **WHEN** PdfCell 的 bbox 覆盖多行多列
- **THEN** `pdf_generator.py` 使用该完整 bbox 绘制白色背景和文本
- **AND** 文本居中于完整 bbox 区域

## MODIFIED Requirements

### Requirement: extract_tables_by_pymupdf 单元格构建逻辑

修改 `extract_tables_by_pymupdf` 中第 365-404 行的单元格构建逻辑：

**当前逻辑**（均匀分割）：
```python
for row_idx, row in enumerate(data):
    for col_idx, text in enumerate(row):
        cell_bbox = calculate_cell_bbox(bbox_tuple, row_idx, col_idx, len(data), len(row))
        cell_info = create_cell_info(text, cell_bbox, row_idx, col_idx)
```

**新逻辑**（使用真实 bbox）：
```python
if table_cell_bboxes:
    # 使用 PyMuPDF 真实单元格 bbox
    bbox_matrix = _build_bbox_matrix(rows_data, num_rows, num_cols)
    for row_idx, row in enumerate(data):
        for col_idx, text in enumerate(row):
            cell_bbox = bbox_matrix[row_idx][col_idx]
            if cell_bbox is None:
                cell_bbox = calculate_cell_bbox(bbox_tuple, row_idx, col_idx, len(data), len(row))
            cell_info = create_cell_info(text, cell_bbox, row_idx, col_idx)
else:
    # 回退：均匀分割
    for row_idx, row in enumerate(data):
        for col_idx, text in enumerate(row):
            cell_bbox = calculate_cell_bbox(bbox_tuple, row_idx, col_idx, len(data), len(row))
            cell_info = create_cell_info(text, cell_bbox, row_idx, col_idx)
```

### Requirement: row_heights 和 col_widths 计算逻辑

**当前逻辑**（从均匀分割的 cell 尺寸计算）：
```python
row_heights_list = calculate_row_heights(cell_matrix)
col_widths_list = calculate_col_widths(cell_matrix, bbox_tuple)
```

**新逻辑**（从真实 bbox 推算）：
```python
if table_cell_bboxes:
    row_heights_list = calculate_row_heights_from_bboxes(bbox_matrix)
    col_widths_list = calculate_col_widths_from_bboxes(bbox_matrix, bbox_tuple)
else:
    row_heights_list = calculate_row_heights(cell_matrix)
    col_widths_list = calculate_col_widths(cell_matrix, bbox_tuple)
```

## REMOVED Requirements

无（均匀分割作为 fallback 保留）
