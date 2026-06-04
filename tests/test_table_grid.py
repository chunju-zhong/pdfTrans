#!/usr/bin/env python3
"""Test _compute_table_grid grid layout logic"""
from modules.ocr.paddle_extractor import PaddleOcrExtractor
from models.extraction import PdfCell


def test_grid_uniform_rows():
    """同一行所有单元格的 y0 和 y1 必须相同"""
    table_bbox = (100, 100, 500, 300)  # 2 rows, 3 cols
    cells = [
        [PdfCell('A', (0,0,0,0), 0, 0), PdfCell('B', (0,0,0,0), 0, 1), PdfCell('C', (0,0,0,0), 0, 2)],
        [PdfCell('D', (0,0,0,0), 1, 0), PdfCell('E', (0,0,0,0), 1, 1), PdfCell('F', (0,0,0,0), 1, 2)],
    ]
    textline_boxes = [
        [110, 115, 180, 130],  # row0 col0
        [220, 112, 310, 128],  # row0 col1
        [330, 118, 440, 135],  # row0 col2
        [110, 210, 190, 230],  # row1 col0
        [220, 215, 300, 228],  # row1 col1
        [330, 212, 450, 232],  # row1 col2
    ]
    textline_texts = ['A', 'B', 'C', 'D', 'E', 'F']

    result_cells, row_heights, col_widths = PaddleOcrExtractor._compute_table_grid(
        table_bbox, cells, textline_boxes, textline_texts
    )

    # 同一行的 y0, y1 必须相同
    for row in result_cells:
        y0_set = set(cell.bbox[1] for cell in row)
        y1_set = set(cell.bbox[3] for cell in row)
        assert len(y0_set) == 1, f"同行 y0 不一致: {y0_set}"
        assert len(y1_set) == 1, f"同行 y1 不一致: {y1_set}"

    # 同一列的 x0, x1 必须相同
    for col_idx in range(3):
        x0_set = set(result_cells[r][col_idx].bbox[0] for r in range(2))
        x1_set = set(result_cells[r][col_idx].bbox[2] for r in range(2))
        assert len(x0_set) == 1, f"同列 x0 不一致: {x0_set}"
        assert len(x1_set) == 1, f"同列 x1 不一致: {x1_set}"

    print(f"row_heights: {row_heights}")
    print(f"col_widths: {col_widths}")
    print("Test grid_uniform_rows PASSED")


def test_grid_no_textline():
    """无 textline 数据时返回空列表"""
    table_bbox = (100, 100, 500, 300)
    cells = [[PdfCell('A', (0,0,0,0), 0, 0)]]
    result, rh, cw = PaddleOcrExtractor._compute_table_grid(table_bbox, cells, None, [])
    assert rh == [] and cw == []
    print("Test grid_no_textline PASSED")


def test_grid_empty_cells():
    """cells 为空时返回空列表"""
    result, rh, cw = PaddleOcrExtractor._compute_table_grid((0,0,100,100), [], [1,2,3], ['a'])
    assert rh == [] and cw == []
    print("Test grid_empty_cells PASSED")


if __name__ == '__main__':
    test_grid_uniform_rows()
    test_grid_no_textline()
    test_grid_empty_cells()
    print("\nAll tests PASSED!")
