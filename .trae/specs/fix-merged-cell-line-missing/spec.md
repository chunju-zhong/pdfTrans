# 修复合并单元格误判导致横线缺失 Spec

## Why

第20页表格第5行和第6行之间的横线没有绘制。根因：PyMuPDF 路径中用 `cell_height > uniform_row_height * 1.5` 阈值检测合并单元格，可能将行高稍大的普通单元格误判为 `row_span=2`，导致网格线遮挡逻辑错误地跳过了该行边界处的横线。

PyMuPDF 已经通过 `cell_bbox is None` 正确标记了合并单元格的被合并位置，1.5 倍阈值的额外检测是多余的且容易误判。

## What Changes

- 移除 PyMuPDF 路径中基于 1.5 倍阈值的 span 检测逻辑
- 改为仅依赖 `cell_bbox is None` 来推断合并单元格的 `row_span`/`col_span`
- 新增 `_compute_span_from_none_positions` 函数，从 `bbox_matrix` 中的 None 位置反推合并单元格的 span

## Impact

- Affected specs: `optimize-merged-cell-rendering`
- Affected code: `modules/extractors/table_processor.py`

## ADDED Requirements

### Requirement: 基于 None 位置推断合并单元格 span

PyMuPDF 路径 SHALL 从 `bbox_matrix` 中 `None` 的分布来推断合并单元格的 `row_span` 和 `col_span`，而非使用 1.5 倍阈值。

#### Scenario: 合并单元格跨 2 行 1 列

- **WHEN** `bbox_matrix` 中 `(row, col)` 有有效 bbox，而 `(row+1, col)` 为 None
- **THEN** `(row, col)` 处的 `PdfCell.row_span = 2`，`(row+1, col)` 处设为 None

#### Scenario: 合并单元格跨 1 行 2 列

- **WHEN** `bbox_matrix` 中 `(row, col)` 有有效 bbox，而 `(row, col+1)` 为 None
- **THEN** `(row, col)` 处的 `PdfCell.col_span = 2`，`(row, col+1)` 处设为 None

#### Scenario: 普通单元格

- **WHEN** `bbox_matrix` 中某位置有有效 bbox，且其右侧和下方均无 None
- **THEN** `row_span = 1, col_span = 1`

## MODIFIED Requirements

### Requirement: 移除 1.5 倍阈值 span 检测

删除 `table_processor.py` 中基于 `cell_height > uniform_row_height * 1.5` 和 `cell_width > uniform_col_width * 1.5` 的 span 检测代码（第 433-466 行），替换为基于 `bbox_matrix` 中 None 位置的推断。

推断算法：

```python
def _compute_span_from_none_positions(bbox_matrix, num_rows, num_cols):
    """从 bbox_matrix 中 None 的位置推断合并单元格的 row_span/col_span

    对于每个有有效 bbox 的位置，向右和向下扫描连续的 None，
    确定该单元格的 col_span 和 row_span。

    Returns:
        dict: {(row_idx, col_idx): (row_span, col_span)}
    """
    span_map = {}

    for row_idx in range(num_rows):
        for col_idx in range(num_cols):
            if row_idx >= len(bbox_matrix) or col_idx >= len(bbox_matrix[row_idx]):
                continue
            if bbox_matrix[row_idx][col_idx] is None:
                continue

            # 向右扫描连续 None，确定 col_span
            col_span = 1
            c = col_idx + 1
            while c < num_cols and c < len(bbox_matrix[row_idx]) and bbox_matrix[row_idx][c] is None:
                # 验证：这个 None 确实是被 (row_idx, col_idx) 合并的，
                # 而不是被上方某个单元格合并的
                # 简单策略：如果上方也是 None 或上方单元格的 col_span 覆盖此位置，则跳过
                col_span += 1
                c += 1

            # 向下扫描连续 None，确定 row_span
            row_span = 1
            r = row_idx + 1
            while r < num_rows and r < len(bbox_matrix) and col_idx < len(bbox_matrix[r]) and bbox_matrix[r][col_idx] is None:
                row_span += 1
                r += 1

            if row_span > 1 or col_span > 1:
                span_map[(row_idx, col_idx)] = (row_span, col_span)

    return span_map
```

调用方式替换原来的阈值检测：

```python
# 替换原来的 uniform_row_height / uniform_col_width 阈值检测
span_map = _compute_span_from_none_positions(bbox_matrix, num_rows, num_cols)

for row_idx, row in enumerate(data):
    for col_idx, text in enumerate(row):
        if use_real_bbox and row_idx < len(bbox_matrix) and col_idx < len(bbox_matrix[row_idx]):
            cell_bbox = bbox_matrix[row_idx][col_idx]
            if cell_bbox is None:
                continue
        # ...

        # 使用 span_map 获取 span，不再用阈值
        row_span, col_span = span_map.get((row_idx, col_idx), (1, 1))

        pdf_cell = create_pdf_cell(cell_info, row_span=row_span, col_span=col_span)
        # ...
```

## REMOVED Requirements

无
