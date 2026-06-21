# -*- coding: utf-8 -*-
"""表格布局优化相关功能的单元测试

覆盖三个核心变更：
1. PdfCell.estimated_lines 字段的序列化/反序列化
2. LlmOcrExtractor._compute_table_layout 静态方法的布局计算
3. PdfGenerator._preprocess_latex_for_mathtext 静态方法的LaTeX环境去除
"""

import pytest
import math
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.extraction import PdfCell
from modules.ocr.llm_extractor import LlmOcrExtractor, _estimate_text_display_width
from modules.pdf_generator import PdfGenerator


# ============================================================
# 1. PdfCell estimated_lines 字段测试
# ============================================================

class TestPdfCellEstimatedLines:
    """PdfCell.estimated_lines 字段的序列化与默认值测试"""

    def test_default_estimated_lines_is_zero(self):
        """默认estimated_lines为0"""
        cell = PdfCell(text="test", bbox=(0, 0, 100, 30), row_idx=0, col_idx=0)
        assert cell.estimated_lines == 0

    def test_estimated_lines_set_in_constructor(self):
        """构造函数可设置estimated_lines"""
        cell = PdfCell(text="test", bbox=(0, 0, 100, 30), row_idx=0, col_idx=0, estimated_lines=3)
        assert cell.estimated_lines == 3

    def test_to_dict_includes_estimated_lines(self):
        """to_dict包含estimated_lines字段"""
        cell = PdfCell(text="test", bbox=(0, 0, 100, 30), row_idx=0, col_idx=0, estimated_lines=2)
        d = cell.to_dict()
        assert 'estimated_lines' in d
        assert d['estimated_lines'] == 2

    def test_from_dict_reads_estimated_lines(self):
        """from_dict读取estimated_lines字段"""
        data = {'text': 'test', 'bbox': [0, 0, 100, 30], 'row_idx': 0, 'col_idx': 0, 'estimated_lines': 4}
        cell = PdfCell.from_dict(data)
        assert cell.estimated_lines == 4

    def test_from_dict_default_estimated_lines(self):
        """from_dict中estimated_lines默认为0"""
        data = {'text': 'test', 'bbox': [0, 0, 100, 30], 'row_idx': 0, 'col_idx': 0}
        cell = PdfCell.from_dict(data)
        assert cell.estimated_lines == 0


# ============================================================
# 2. _compute_table_layout 测试
# ============================================================

class TestComputeTableLayout:
    """LlmOcrExtractor._compute_table_layout 静态方法的布局计算测试"""

    @staticmethod
    def _make_matrix(data):
        """创建测试用单元格矩阵

        Args:
            data: 二维文本列表，每个元素为单元格文本

        Returns:
            二维 PdfCell 列表
        """
        matrix = []
        for r, row in enumerate(data):
            cell_row = []
            for c, text in enumerate(row):
                cell = PdfCell(text=text, bbox=(0, 0, 0, 0), row_idx=r, col_idx=c)
                cell_row.append(cell)
            matrix.append(cell_row)
        return matrix

    def test_equal_content_equal_width(self):
        """内容长度相同时列宽相等"""
        matrix = self._make_matrix([["AA", "BB"], ["CC", "DD"]])
        col_widths, row_heights, _, _ = LlmOcrExtractor._compute_table_layout(
            matrix, 2, 2, (0, 0, 400, 100)
        )
        # 两个单元格内容长度相近，列宽应接近
        assert abs(col_widths[0] - col_widths[1]) < 50

    def test_long_content_gets_wider_column(self):
        """长内容的列获得更宽的列宽"""
        matrix = self._make_matrix([["短", "这是一个很长的数据源描述文本"], ["A", "另一个很长的描述"]])
        col_widths, row_heights, _, _ = LlmOcrExtractor._compute_table_layout(
            matrix, 2, 2, (0, 0, 400, 100)
        )
        # 第二列内容更长，应获得更宽的列宽
        assert col_widths[1] > col_widths[0]

    def test_total_width_matches_bbox(self):
        """列宽总和等于表格宽度"""
        matrix = self._make_matrix([["A", "B", "C"], ["D", "E", "F"]])
        col_widths, _, _, _ = LlmOcrExtractor._compute_table_layout(
            matrix, 2, 3, (0, 0, 360, 100)
        )
        assert abs(sum(col_widths) - 360) < 0.1

    def test_total_height_within_bbox(self):
        """行高总和不超过bbox高度"""
        matrix = self._make_matrix([["A", "B"], ["C", "D"]])
        _, row_heights, _, _ = LlmOcrExtractor._compute_table_layout(
            matrix, 2, 2, (0, 0, 400, 100)
        )
        assert sum(row_heights) <= 100.01  # 允许浮点误差

    def test_column_width_clamped_min_10_percent(self):
        """列宽最小10%"""
        matrix = self._make_matrix([["A", "BBBBBBBBBBBBBBBBBBBBBBBBBB"], ["C", "DDDDDDDDDDDDDDDDDDDDDDDDDD"]])
        col_widths, _, _, _ = LlmOcrExtractor._compute_table_layout(
            matrix, 2, 2, (0, 0, 400, 100)
        )
        min_width = 400 * 0.1
        for w in col_widths:
            assert w >= min_width - 0.1

    def test_column_width_clamped_max_50_percent(self):
        """列宽最大50%"""
        matrix = self._make_matrix([["A", "B"], ["C", "D"]])
        col_widths, _, _, _ = LlmOcrExtractor._compute_table_layout(
            matrix, 2, 2, (0, 0, 400, 100)
        )
        max_width = 400 * 0.5
        for w in col_widths:
            assert w <= max_width + 0.1

    def test_empty_cells_estimated_lines_zero(self):
        """空单元格的estimated_lines为0"""
        matrix = self._make_matrix([["", "B"], ["C", ""]])
        LlmOcrExtractor._compute_table_layout(matrix, 2, 2, (0, 0, 400, 100))
        assert matrix[0][0].estimated_lines == 0
        assert matrix[1][1].estimated_lines == 0

    def test_text_cells_estimated_lines_positive(self):
        """有文本的单元格的estimated_lines > 0"""
        matrix = self._make_matrix([["Hello", "World"], ["Foo", "Bar"]])
        LlmOcrExtractor._compute_table_layout(matrix, 2, 2, (0, 0, 400, 100))
        for row in matrix:
            for cell in row:
                if cell.text:
                    assert cell.estimated_lines > 0

    def test_row_height_priority_over_column_width(self):
        """行高优先：长文本行获得更多高度"""
        matrix = self._make_matrix([["短"], ["这是一个非常长的文本内容需要换行才能显示完整"]])
        _, row_heights, _, _ = LlmOcrExtractor._compute_table_layout(
            matrix, 2, 1, (0, 0, 100, 80)
        )
        # 长文本行应比短文本行更高
        assert row_heights[1] > row_heights[0]

    def test_single_cell_table(self):
        """单单元格表格：列宽受max_col_ratio=50%限制，不超过表格宽度50%"""
        matrix = self._make_matrix([["Only cell"]])
        col_widths, row_heights, t_x0, t_y0 = LlmOcrExtractor._compute_table_layout(
            matrix, 1, 1, (10, 20, 310, 60)
        )
        # 单列受 max_col_ratio=0.5 限制，列宽 = 300 * 0.5 = 150
        assert abs(col_widths[0] - 150.0) < 0.1
        assert abs(sum(row_heights) - 40) < 0.1
        assert t_x0 == 10
        assert t_y0 == 20


# ============================================================
# 3. LaTeX 环境去除测试
# ============================================================

class TestLatexEnvironmentRemoval:
    """PdfGenerator._preprocess_latex_for_mathtext 静态方法的LaTeX环境去除测试"""

    def test_aligned_environment_removed(self):
        r"""\begin{aligned}...\end{aligned}环境被去除"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\begin{aligned}&=34+44+46\end{aligned}'
        )
        assert r'\begin{aligned}' not in result
        assert r'\end{aligned}' not in result

    def test_cases_environment_removed(self):
        r"""\begin{cases}...\end{cases}环境被去除"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\begin{cases}x & \text{if } a > 0 \\ -x & \text{otherwise}\end{cases}'
        )
        assert r'\begin{cases}' not in result
        assert r'\end{cases}' not in result

    def test_equation_star_environment_removed(self):
        r"""\begin{equation*}...\end{equation*}环境被去除"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\begin{equation*}E = mc^2\end{equation*}'
        )
        assert r'\begin{equation*}' not in result
        assert r'\end{equation*}' not in result

    def test_gather_star_environment_removed(self):
        r"""\begin{gather*}...\end{gather*}环境被去除"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\begin{gather*}a + b \\ c + d\end{gather*}'
        )
        assert r'\begin{gather*}' not in result
        assert r'\end{gather*}' not in result

    def test_idempotent_environment_removal(self):
        """环境去除是幂等的"""
        latex = r'\begin{aligned}&=34+44+46\end{aligned}'
        result1 = PdfGenerator._preprocess_latex_for_mathtext(latex)
        result2 = PdfGenerator._preprocess_latex_for_mathtext(result1)
        assert result1 == result2

    def test_align_star_environment_removed(self):
        r"""\begin{align*}...\end{align*}环境被去除"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\begin{align*}a &= b + c \\ d &= e + f\end{align*}'
        )
        assert r'\begin{align*}' not in result
        assert r'\end{align*}' not in result

    def test_gathered_environment_removed(self):
        r"""\begin{gathered}...\end{gathered}环境被去除"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\begin{gathered}a + b \\ c + d\end{gathered}'
        )
        assert r'\begin{gathered}' not in result
        assert r'\end{gathered}' not in result

    def test_double_backslash_replaced_with_space(self):
        r"""环境内的 \\ 行分隔符被替换为空格"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\begin{aligned}a \\ b\end{aligned}'
        )
        assert '\\\\' not in result
        # 内容应保留（a 和 b）
        assert 'a' in result
        assert 'b' in result

    def test_alignment_ampersand_removed(self):
        r"""环境内的 & 对齐标记被去除"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\begin{aligned}a &= b\end{aligned}'
        )
        # & 对齐标记应被去除
        assert '&' not in result

    def test_display_math_delimiter_conversion(self):
        r"""$$...$$ 转换为 $...$"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'$$E = mc^2$$'
        )
        assert result.startswith('$') and not result.startswith('$$')

    def test_inline_math_delimiter_conversion(self):
        r"""\(...\) 转换为 $...$"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\(x + y\)'
        )
        assert r'\(' not in result
        assert r'\)' not in result

    def test_greek_letter_replacement(self):
        r"""希腊字母命令被替换为Unicode字符"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\alpha + \beta'
        )
        assert 'α' in result
        assert 'β' in result
        assert r'\alpha' not in result
        assert r'\beta' not in result

    def test_left_right_commands_removed(self):
        r"""\left 和 \right 命令被去除"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\left(3 \times 23\right)'
        )
        assert r'\left' not in result
        assert r'\right' not in result

    def test_text_command_removed(self):
        r"""\text{content} 被替换为 content"""
        result = PdfGenerator._preprocess_latex_for_mathtext(
            r'\text{if } a > 0'
        )
        assert r'\text' not in result
        assert 'if' in result


# ============================================================
# 4. _estimate_text_display_width 辅助函数测试
# ============================================================

class TestEstimateTextDisplayWidth:
    """_estimate_text_display_width 辅助函数测试"""

    def test_ascii_width(self):
        """ASCII字符宽度为font_size * 0.6"""
        width = _estimate_text_display_width("AB", font_size=10.0)
        assert abs(width - 10.0 * 0.6 * 2) < 0.01

    def test_cjk_width(self):
        """CJK字符宽度为font_size * 1.0"""
        width = _estimate_text_display_width("你好", font_size=10.0)
        assert abs(width - 10.0 * 1.0 * 2) < 0.01

    def test_mixed_width(self):
        """混合字符宽度正确计算"""
        width = _estimate_text_display_width("A你", font_size=10.0)
        expected = 10.0 * 0.6 + 10.0 * 1.0
        assert abs(width - expected) < 0.01

    def test_empty_string(self):
        """空字符串宽度为0"""
        width = _estimate_text_display_width("", font_size=10.0)
        assert width == 0.0

    def test_default_font_size(self):
        """默认font_size为9.0"""
        width = _estimate_text_display_width("A", font_size=9.0)
        assert abs(width - 9.0 * 0.6) < 0.01

    def test_fullwidth_width(self):
        """全角字符宽度为font_size * 1.0"""
        width = _estimate_text_display_width("Ａ", font_size=10.0)
        assert abs(width - 10.0 * 1.0) < 0.01
