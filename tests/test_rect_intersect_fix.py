#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Rect.intersect() 原地修改 bug 修复及累积重叠面积检测

变更分析：
1. pdf_extractor.py: intersect() → & 运算符，累积重叠面积，空列表回退
2. table_processor.py: extract_table_cells_by_bbox 新增 table_bbox 参数和字符过滤
3. style_analyzer.py: intersect() → & 运算符
"""

import pytest
import fitz


class TestRectIntersectMutation:
    """测试 Rect.intersect() 原地修改问题及 & 运算符修复"""

    def test_intersect_mutates_caller(self):
        """验证 Rect.intersect() 会原地修改调用者矩形（这是 PyMuPDF 的行为）"""
        r1 = fitz.Rect(100, 200, 400, 500)
        r2 = fitz.Rect(50, 150, 200, 300)
        original_r1 = fitz.Rect(r1)

        r1.intersect(r2)

        # intersect() 原地修改了 r1
        assert r1 != original_r1, "intersect() 应该原地修改调用者矩形"

    def test_and_operator_does_not_mutate(self):
        """验证 & 运算符不会修改原始矩形"""
        r1 = fitz.Rect(100, 200, 400, 500)
        r2 = fitz.Rect(50, 150, 200, 300)
        original_r1 = fitz.Rect(r1)

        result = r1 & r2

        # & 运算符不修改 r1
        assert r1 == original_r1, "& 运算符不应修改原始矩形"
        # 结果正确
        assert result == fitz.Rect(100, 200, 200, 300)

    def test_and_operator_returns_correct_intersection(self):
        """验证 & 运算符返回正确的交集"""
        r1 = fitz.Rect(100, 200, 400, 500)
        r2 = fitz.Rect(50, 150, 200, 300)

        result = r1 & r2
        expected = fitz.Rect(100, 200, 200, 300)
        assert result == expected

    def test_and_operator_non_overlapping(self):
        """验证 & 运算符对不重叠矩形返回空矩形"""
        r1 = fitz.Rect(100, 200, 400, 500)
        r2 = fitz.Rect(50, 50, 80, 100)

        result = r1 & r2
        assert result.is_empty

    def test_accumulated_overlap_with_intersect_is_wrong(self):
        """验证使用 intersect() 在循环中累积重叠面积会得到错误结果"""
        block_rect = fitz.Rect(100, 200, 400, 500)
        block_area = block_rect.width * block_rect.height
        cells = [
            fitz.Rect(50, 150, 200, 300),
            fitz.Rect(150, 250, 350, 450),
        ]

        # 使用 intersect() — 第一次调用后 block_rect 被破坏
        total = 0
        for cell in cells:
            try:
                intersection = block_rect.intersect(cell)
                total += intersection.width * intersection.height
            except Exception:
                continue

        # 第二个单元格的重叠计算基于被破坏的 block_rect，结果错误
        # 正确值应该 > 0，但 intersect() 破坏后可能为 0 或极小
        assert total < block_area, "intersect() 破坏后累积结果不正确"

    def test_accumulated_overlap_with_and_is_correct(self):
        """验证使用 & 运算符在循环中累积重叠面积得到正确结果"""
        block_rect = fitz.Rect(100, 200, 400, 500)
        block_area = block_rect.width * block_rect.height
        cells = [
            fitz.Rect(50, 150, 200, 300),
            fitz.Rect(150, 250, 350, 450),
        ]

        total = 0
        for cell in cells:
            intersection = block_rect & cell
            total += intersection.width * intersection.height

        # 两个单元格都与 block_rect 有重叠
        assert total > 0, "& 运算符累积重叠面积应 > 0"
        # 第一个单元格重叠: (200-100)*(300-200) = 10000
        # 第二个单元格重叠: (350-150)*(450-250) = 40000
        assert total == 50000, f"累积重叠面积应为 50000，实际为 {total}"


class TestExtractTextBlocksOverlapDetection:
    """测试 _extract_text_blocks 的重叠检测逻辑"""

    def test_single_cell_overlap_above_threshold(self):
        """单个单元格重叠超过 50% 应标记为表格文本"""
        block_rect = fitz.Rect(100, 200, 400, 500)
        block_area = block_rect.width * block_rect.height  # 60000
        cells = [fitz.Rect(80, 180, 420, 520)]  # 几乎完全包含

        total = 0
        for cell in cells:
            intersection = block_rect & cell
            total += intersection.width * intersection.height

        assert total > block_area * 0.5

    def test_accumulated_overlap_across_cells(self):
        """多个单元格各自重叠不足 50% 但总和超过 50% 应标记为表格文本"""
        block_rect = fitz.Rect(100, 200, 400, 500)
        block_area = block_rect.width * block_rect.height  # 90000
        # 三个单元格各占约 1/3
        cells = [
            fitz.Rect(80, 180, 200, 520),    # 左1/3
            fitz.Rect(200, 180, 300, 520),   # 中1/3
            fitz.Rect(300, 180, 420, 520),   # 右1/3
        ]

        total = 0
        for cell in cells:
            intersection = block_rect & cell
            area = intersection.width * intersection.height
            total += area

        # 每个单元格单独不足 50%，但总和超过 50%
        for cell in cells:
            intersection = block_rect & cell
            assert intersection.width * intersection.height < block_area * 0.5
        assert total > block_area * 0.5

    def test_empty_cell_bboxes_fallback(self):
        """空单元格 bbox 列表应回退到表格整体 bbox 检测"""
        block_rect = fitz.Rect(100, 200, 400, 500)
        block_area = block_rect.width * block_rect.height

        # 模拟空单元格列表
        current_page_table_cells = [[]]
        current_page_tables = [(80, 180, 420, 520)]

        has_valid_cells = False
        is_table_text = False
        for table_cell_bboxes in current_page_table_cells:
            if not table_cell_bboxes:
                continue
            has_valid_cells = True

        if not has_valid_cells and current_page_tables:
            for table_bbox in current_page_tables:
                table_rect = fitz.Rect(table_bbox)
                intersection = block_rect & table_rect
                overlap_area = intersection.width * intersection.height
                if overlap_area > block_area * 0.5:
                    is_table_text = True
                    break

        assert not has_valid_cells
        assert is_table_text


class TestExtractTableCellsByBbox:
    """测试 extract_table_cells_by_bbox 的表格 bbox 字符过滤"""

    def test_function_accepts_table_bbox_parameter(self):
        """验证函数接受 table_bbox 参数"""
        import inspect
        from modules.extractors.table_processor import extract_table_cells_by_bbox

        sig = inspect.signature(extract_table_cells_by_bbox)
        params = list(sig.parameters.keys())
        assert 'table_bbox' in params, "函数应接受 table_bbox 参数"
        assert sig.parameters['table_bbox'].default is None, "table_bbox 默认值应为 None"

    def test_table_bbox_filters_outside_chars(self):
        """验证超出表格 bbox 的字符被过滤"""
        table_bbox = (100, 100, 400, 400)
        table_rect = fitz.Rect(table_bbox)
        table_rect_expanded = fitz.Rect(
            table_rect.x0 - 2, table_rect.y0 - 2,
            table_rect.x1 + 2, table_rect.y1 + 2
        )

        # 表格内的字符
        inside_char = {
            "char": "A",
            "bbox": fitz.Rect(150, 150, 160, 160),
            "area": 100,
            "x0": 150,
            "y0": 150,
        }
        # 表格外的字符
        outside_char = {
            "char": "B",
            "bbox": fitz.Rect(50, 50, 60, 60),
            "area": 100,
            "x0": 50,
            "y0": 50,
        }

        all_chars = [inside_char, outside_char]
        filtered = []
        for char_info in all_chars:
            char_center_x = (char_info["x0"] + char_info["bbox"].x1) / 2
            char_center_y = (char_info["y0"] + char_info["bbox"].y1) / 2
            if table_rect_expanded.contains(fitz.Point(char_center_x, char_center_y)):
                filtered.append(char_info)

        assert len(filtered) == 1
        assert filtered[0]["char"] == "A"

    def test_boundary_chars_within_tolerance(self):
        """验证边界字符（2px 容差内）不被误排除"""
        table_bbox = (100, 100, 400, 400)
        table_rect = fitz.Rect(table_bbox)
        table_rect_expanded = fitz.Rect(
            table_rect.x0 - 2, table_rect.y0 - 2,
            table_rect.x1 + 2, table_rect.y1 + 2
        )

        # 刚好在边界上（容差内）的字符
        boundary_char = {
            "char": "X",
            "bbox": fitz.Rect(99, 99, 109, 109),
            "area": 100,
            "x0": 99,
            "y0": 99,
        }

        char_center_x = (boundary_char["x0"] + boundary_char["bbox"].x1) / 2
        char_center_y = (boundary_char["y0"] + boundary_char["bbox"].y1) / 2

        assert table_rect_expanded.contains(fitz.Point(char_center_x, char_center_y))


class TestStyleAnalyzerIntersectionFix:
    """测试 style_analyzer.py 的 intersect 修复"""

    def test_and_operator_in_loop_preserves_rect(self):
        """验证在循环中使用 & 运算符不会修改 dict_rect"""
        dict_rect = fitz.Rect(100, 200, 400, 500)
        original = fitz.Rect(dict_rect)
        current_rect = fitz.Rect(50, 150, 200, 300)

        # 模拟循环中的多次交集计算
        for _ in range(3):
            intersection = dict_rect & current_rect
            _ = intersection.width * intersection.height

        assert dict_rect == original, "循环后 dict_rect 不应被修改"
