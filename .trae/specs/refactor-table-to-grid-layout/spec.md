# 重构表格单元格为统一网格布局 Spec

## Why

之前 `_compute_cell_bboxes` 为每个单元格独立计算 tight bbox，导致：

1. **字体大小不一**：`pdf_generator.py` 第 626 行 `base_font_size = min(cell_height * 0.8, 12)` — 每个单元格 bbox 高度不同，算出的字体大小各不相同
2. **表格线条混乱**：`pdf_generator.py` 第 603 行每个单元格独立绘制边框 — 当单元格 bbox 不共享网格线时，边框不重合，出现重叠线条、间隙和错位

根因：表格是**网格结构**（同行等高、同列等宽），但 tight bbox 方案把每个单元格当作独立区域，破坏了网格一致性。

## What Changes

1. **废弃 `_compute_cell_bboxes`** 的 tight bbox 方案，改用**统一网格布局**
2. 新增 `_compute_table_grid` 方法：从 textline bbox 计算每行的统一行高、每列的统一列宽
3. 在表格处理中，为每个单元格计算网格位置（基于累积行高/列宽），并设置 `cell.bbox`、`table.row_heights`、`table.col_widths`

## Impact

- Affected specs: `improve-bbox-accuracy-using-textlines`、`fix-cell-bbox-coordinate-mismatch`
- Affected code: `modules/ocr/paddle_extractor.py`（`_compute_cell_bboxes`、表格处理逻辑）、`models/extraction.py`（PdfTable 已有 row_heights/col_widths）

## ADDED Requirements

### Requirement: 表格单元格统一网格布局

系统在提取表格后，SHALL 为所有单元格计算一致的网格位置，确保同行单元格具有相同的高度和垂直位置，同列单元格具有相同的宽度和水平位置。

#### Scenario: textline 数据可用

- **WHEN** 表格区域内有 `textline_boxes`
- **THEN** 系统按行列区域分组 textline，计算每行的统一行高（该行内所有 textline 的最小 y1 到最大 y2）
- **AND** 计算每列的统一列宽（该列内所有 textline 的最小 x1 到最大 x2）
- **AND** 基于累积行高/列宽为每个单元格计算网格 bbox

#### Scenario: 行或列内无 textline

- **WHEN** 某行或某列内没有匹配到的 textline
- **THEN** 该行/列使用平均行高/列宽作为 fallback

### Requirement: 设置 PdfTable 的 row_heights 和 col_widths

系统将计算出的行高和列宽设置到 `PdfTable.row_heights` 和 `PdfTable.col_widths`，供 `pdf_generator.py` 的备用路径使用。

## MODIFIED Requirements

### Requirement: 替换 `_compute_cell_bboxes` 为 `_compute_table_grid`

将现有的 `_compute_cell_bboxes` 方法替换为新的 `_compute_table_grid` 方法：

```python
@staticmethod
def _compute_table_grid(table_pixel_bbox, cells, textline_boxes, textline_texts):
    """为表格计算统一网格布局，更新单元格 bbox 和行列尺寸

    Args:
        table_pixel_bbox: 表格的像素坐标 bbox (x1,y1,x2,y2)
        cells: list[list[PdfCell]] 二维单元格列表
        textline_boxes: textline bbox 列表
        textline_texts: textline 文本列表

    Returns:
        tuple: (cells, row_heights, col_widths)
            - cells: 更新了 bbox 的单元格列表
            - row_heights: 每行的统一高度列表
            - col_widths: 每列的统一宽度列表
    """
    if not cells or textline_boxes is None or len(textline_boxes) == 0:
        return cells, [], []

    tx1, ty1, tx2, ty2 = table_pixel_bbox
    n_rows = len(cells)
    n_cols = max(len(row) for row in cells) if cells else 0
    if n_rows == 0 or n_cols == 0:
        return cells, [], []

    # 计算均匀行列区域
    row_height = (ty2 - ty1) / n_rows
    col_width = (tx2 - tx1) / n_cols

    # 收集每行/列的 textline bbox
    row_tight = [None] * n_rows  # (min_y1, max_y2)
    col_tight = [None] * n_cols  # (min_x1, max_x2)

    for row_idx in range(n_rows):
        cell_y1 = ty1 + row_idx * row_height
        cell_y2 = ty1 + (row_idx + 1) * row_height

        for col_idx in range(n_cols):
            cell_x1 = tx1 + col_idx * col_width
            cell_x2 = tx1 + (col_idx + 1) * col_width

            for tl_box in textline_boxes:
                if len(tl_box) < 4:
                    continue
                bx, by, bx2, by2 = float(tl_box[0]), float(tl_box[1]), float(tl_box[2]), float(tl_box[3])
                cx, cy = (bx+bx2)/2, (by+by2)/2
                if cell_x1 <= cx <= cell_x2 and cell_y1 <= cy <= cell_y2:
                    # 更新行 tight
                    if row_tight[row_idx] is None:
                        row_tight[row_idx] = (by, by2)
                    else:
                        row_tight[row_idx] = (min(row_tight[row_idx][0], by), max(row_tight[row_idx][1], by2))
                    # 更新列 tight
                    if col_tight[col_idx] is None:
                        col_tight[col_idx] = (bx, bx2)
                    else:
                        col_tight[col_idx] = (min(col_tight[col_idx][0], bx), max(col_tight[col_idx][1], bx2))

    # 计算最终行高和列宽（textline tight 优先，否则用平均）
    row_heights = []
    for i in range(n_rows):
        if row_tight[i]:
            h = max(row_tight[i][1] - row_tight[i][0], row_height * 0.5)
        else:
            h = row_height
        row_heights.append(h)

    col_widths = []
    for j in range(n_cols):
        if col_tight[j]:
            w = max(col_tight[j][1] - col_tight[j][0], col_width * 0.5)
        else:
            w = col_width
        col_widths.append(w)

    # 为每个单元格计算网格 bbox（累积行列尺寸）
    for row_idx, row in enumerate(cells):
        grid_y1 = ty1 + sum(row_heights[:row_idx])
        grid_y2 = grid_y1 + row_heights[row_idx]

        for col_idx, cell in enumerate(row):
            grid_x1 = tx1 + sum(col_widths[:col_idx])
            grid_x2 = grid_x1 + col_widths[col_idx]

            cell.bbox = (grid_x1, grid_y1, grid_x2, grid_y2)
            cell.width = grid_x2 - grid_x1
            cell.height = grid_y2 - grid_y1

    return cells, row_heights, col_widths
```

调用点修改（第 615-632 行）：
```python
# 为表格计算统一网格布局
if cells and textline_boxes is not None and len(textline_boxes) > 0:
    cells, row_heights_px, col_widths_px = PaddleOcrExtractor._compute_table_grid(
        bbox, cells, textline_boxes, textline_texts
    )
else:
    row_heights_px = []
    col_widths_px = []

# 将单元格 bbox 从像素坐标转换为 PDF 坐标
for row in cells:
    for cell in row:
        if cell.bbox and cell.bbox != (0, 0, 0, 0):
            cell.bbox = self._pixel_to_pdf_coords(cell.bbox, page_info)
            cell.width = cell.bbox[2] - cell.bbox[0]
            cell.height = cell.bbox[3] - cell.bbox[1]

# 转换行列尺寸并设置到 PdfTable
if row_heights_px and page_info:
    scale = page_info.get('scale_y', 1.0) if 'scale_y' in page_info else ...
    # row_heights 和 col_widths 存为 PDF 点单位
    ...
```

### Requirement: pdf_generator.py 表格绘制优化（可选后续）

当前 `pdf_generator.py` 的 `_draw_translated_table` 中 `base_font_size = min(cell_height * 0.8, 12)` 在统一网格下已经是同行等高，所以字体一致性已自动修复，无需额外改动。

## REMOVED Requirements

### Requirement: `_compute_cell_bboxes` 独立 tight bbox

**Reason**: 独立 tight bbox 破坏了表格网格结构，导致字体不一、线条混乱

**Migration**: 替换为 `_compute_table_grid`，保留 tight bbox 的思想但统一到行列级别
