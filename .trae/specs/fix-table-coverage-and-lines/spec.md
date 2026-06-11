# 表格改网格线画法 + 网格填满 bbox Spec

## Why

两个问题需要同时修复：

1. **线条混乱/缺失**：当前每个单元格独立画 `draw_rect` 边框，共享边画两次、无统一外框
2. **原表格未被完全覆盖**：网格累积行高/列宽 < 表格 bbox 总尺寸，白色背景合起来覆盖不全

## What Changes

1. **`_compute_table_grid`**：缩放行高/列宽使累积值填满表格 bbox（白色背景自然全覆盖）
2. **`_draw_translated_table`**：改用统一网格线画法（外框 + 内部横线/竖线）

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`、`modules/pdf_generator.py`

## ADDED Requirements

### Requirement: 网格填满表格 bbox

`_compute_table_grid` 计算的累积行高 SHALL 等于表格 bbox 的总高度，累积列宽 SHALL 等于表格 bbox 的总宽度。

#### Scenario: 累积尺寸不等于表格尺寸

- **WHEN** 累积行高 < 表格高度 或 累积列宽 < 表格宽度
- **THEN** 按比例缩放各行高和各列宽，使累积值等于表格尺寸

### Requirement: 统一网格线绘制

表格线条 SHALL 使用统一网格线方式绘制：

- 外框：一个 `draw_rect(table_rect, width=1)` 
- 内部水平线：每个行边界 `draw_line`，从左到右，width=0.5
- 内部垂直线：每个列边界 `draw_line`，从上到下，width=0.5
- 行/列边界位置基于 `table.bbox` + `row_heights` / `col_widths` 计算

### Requirement: 白色背景仍由每个单元格绘制

每个单元格的白色背景（`cell_bg_rect`）保持不变，网格填满 bbox 后所有背景合起来覆盖整个原表格区域，不再需要额外背景矩形。

## MODIFIED Requirements

### Requirement: `_compute_table_grid` 缩放逻辑

在计算完 row_heights 和 col_widths 后，添加缩放：

```python
# 确保累积行高/列宽等于表格 bbox 的总高度/总宽度
total_row_height = sum(row_heights)
total_col_width = sum(col_widths)
table_height = ty2 - ty1
table_width = tx2 - tx1

if total_row_height > 0 and abs(total_row_height - table_height) > 1:
    scale_y = table_height / total_row_height
    row_heights = [h * scale_y for h in row_heights]

if total_col_width > 0 and abs(total_col_width - table_width) > 1:
    scale_x = table_width / total_col_width
    col_widths = [w * scale_x for w in col_widths]
```

### Requirement: `_draw_translated_table` 线条绘制修改

删除单元格循环内的 `page.draw_rect(rect, color=(0,0,0), width=0.5)`（第 601-606 行）

在单元格循环后新增统一网格线绘制：

```python
# 统一绘制表格网格线（外框 + 内部线条）
try:
    if table_bbox:
        table_rect = fitz.Rect(table_x0, table_y0, table_x1, table_y1)
        # 外框
        page.draw_rect(table_rect, color=(0, 0, 0), width=1)
        # 内部水平线（每行的底部边界）
        for i in range(len(row_heights) - 1):
            y = table_y0 + sum(row_heights[:i + 1])
            page.draw_line(
                fitz.Point(table_x0, y),
                fitz.Point(table_x1, y),
                color=(0, 0, 0), width=0.5
            )
        # 内部垂直线（每列的右侧边界）
        for j in range(len(col_widths) - 1):
            x = table_x0 + sum(col_widths[:j + 1])
            page.draw_line(
                fitz.Point(x, table_y0),
                fitz.Point(x, table_y1),
                color=(0, 0, 0), width=0.5
            )
except Exception as e:
    logger.error(f"绘制表格网格线异常: {e}")
```

## REMOVED Requirements

无