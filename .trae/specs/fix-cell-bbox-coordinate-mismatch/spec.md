# 修复表格单元格 bbox 坐标空间不匹配 Spec

## Why

`_compute_cell_bboxes` 方法返回的单元格 bbox 是**像素坐标**（因为 `textline_boxes` 来自 PaddleOCR 的像素坐标），但这些值直接存储到 `PdfCell.bbox` 后，`PdfTable` 的 `bbox` 却是**PDF 坐标**（已通过 `_pixel_to_pdf_coords` 转换）。两个坐标空间不匹配，导致 `pdf_generator.py` 使用 `cell.bbox` 绘制表格时位置和大小完全错误。

## What Changes

在 `_compute_cell_bboxes` 返回后，遍历所有单元格，使用 `_pixel_to_pdf_coords` 将每个单元格的 bbox 从像素坐标转换为 PDF 坐标。

## Impact

- Affected specs: `improve-bbox-accuracy-using-textlines`（之前只加了计算，没做坐标转换）
- Affected code: `modules/ocr/paddle_extractor.py`

## ADDED Requirements

### Requirement: 单元格 bbox 坐标转换

在调用 `_compute_cell_bboxes` 后，遍历所有单元格，将每个单元格的 bbox 从像素坐标转换为 PDF 坐标。

#### Scenario: 单元格有有效 bbox

- **WHEN** `_compute_cell_bboxes` 返回了包含非零 bbox 的 cells
- **AND** `page_info` 可用
- **THEN** 遍历每个单元格，调用 `self._pixel_to_pdf_coords(cell.bbox, page_info)` 转换
- **AND** 同时更新 `cell.width` 和 `cell.height`

#### Scenario: 单元格 bbox 仍为零

- **WHEN** 单元格 bbox 为 `(0,0,0,0)`（无 textline 匹配的回退情况）
- **THEN** 跳过转换，保留原始值

## MODIFIED Requirements

### Requirement: paddle_extractor.py 表格单元格 bbox 坐标转换

修改第 615-621 行的表格单元格 bbox 处理代码，在 `_compute_cell_bboxes` 后添加坐标转换：

```python
# 为表格单元格计算精确 bbox
if cells and textline_boxes is not None and len(textline_boxes) > 0:
    cells = PaddleOcrExtractor._compute_cell_bboxes(
        bbox, cells, textline_boxes, textline_texts
    )
    # 将单元格 bbox 从像素坐标转换为 PDF 坐标
    for row in cells:
        for cell in row:
            if cell.bbox and cell.bbox != (0, 0, 0, 0):
                cell.bbox = self._pixel_to_pdf_coords(cell.bbox, page_info)
                cell.width = cell.bbox[2] - cell.bbox[0]
                cell.height = cell.bbox[3] - cell.bbox[1]
    logger.debug(f"[TABLE_CELL] page={page_num}: 表格{idx} 单元格 bbox 已更新 (基于 textline)")
```

## REMOVED Requirements

无