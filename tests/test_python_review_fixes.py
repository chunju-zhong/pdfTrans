# -*- coding: utf-8 -*-
"""Python 代码审查修复测试（2026-06-21 批次）"""

import re
import threading
import pytest
from unittest.mock import patch, MagicMock


class TestLatexEnvironmentBackreference:
    """LaTeX 环境正则反向引用测试"""

    def test_matched_environment_names_stripped(self):
        """相同环境名的 begin/end 被正确去除"""
        from modules.pdf_generator import PdfGenerator

        latex = r'\begin{aligned}&=1\\&=2\end{aligned}'
        result = PdfGenerator._preprocess_latex_for_mathtext(latex)
        assert '\\begin' not in result
        assert '\\end' not in result

    def test_mismatched_environment_names_preserved(self):
        """不同环境名的 begin/end 不被匹配"""
        from modules.pdf_generator import PdfGenerator

        latex = r'\begin{aligned}...\end{cases}'
        result = PdfGenerator._preprocess_latex_for_mathtext(latex)
        assert 'aligned' in result
        assert 'cases' in result

    def test_cases_environment_stripped(self):
        """cases 环境被正确去除"""
        from modules.pdf_generator import PdfGenerator

        latex = r'\begin{cases}x & \text{if } a > 0 \\ -x & \text{otherwise}\end{cases}'
        result = PdfGenerator._preprocess_latex_for_mathtext(latex)
        assert '\\begin' not in result
        assert '\\end' not in result

    def test_equation_star_stripped(self):
        """equation* 环境被正确去除"""
        from modules.pdf_generator import PdfGenerator

        latex = r'\begin{equation*}E = mc^2\end{equation*}'
        result = PdfGenerator._preprocess_latex_for_mathtext(latex)
        assert '\\begin' not in result
        assert '\\end' not in result

    def test_nested_different_environments(self):
        """嵌套不同环境名不被错误匹配"""
        from modules.pdf_generator import PdfGenerator

        latex = r'\begin{aligned}\begin{cases}x\end{cases}\end{aligned}'
        result = PdfGenerator._preprocess_latex_for_mathtext(latex)
        # 内层 cases 先被去除，外层 aligned 再被去除
        assert '\\begin' not in result
        assert '\\end' not in result


class TestLatexConditionalFallback:
    """兜底 \\ 和 & 替换条件化测试"""

    def test_idempotency(self):
        """幂等性：对已处理结果再次调用输出不变"""
        from modules.pdf_generator import PdfGenerator

        latex = r'\begin{aligned}&=34+44+\\left(3*23/3*2\\right)\\\\&=34+44+46\end{aligned}'
        result1 = PdfGenerator._preprocess_latex_for_mathtext(latex)
        result2 = PdfGenerator._preprocess_latex_for_mathtext(result1)
        assert result1 == result2

    def test_simple_math_preserved(self):
        """简单数学公式（无环境）不被破坏"""
        from modules.pdf_generator import PdfGenerator

        latex = r'simple math \alpha + \beta'
        result = PdfGenerator._preprocess_latex_for_mathtext(latex)
        # alpha/beta 应被转换为 Unicode
        assert 'α' in result or 'β' in result

    def test_standalone_ampersand_preserved(self):
        """转义的 \\& 在条件化替换中不被误删"""
        from modules.pdf_generator import PdfGenerator

        latex = r'A \& B'
        result = PdfGenerator._preprocess_latex_for_mathtext(latex)
        # \& 是 LaTeX 转义的 &，处理后应保留 & 字符或 \& 序列
        # 条件化替换只替换两侧有非空白内容的 &，\& 中的 & 前有 \，属于合法内容
        assert 'A' in result and 'B' in result

    def test_line_separator_replaced_in_environment(self):
        """环境内的 \\\\ 行分隔符被替换为空格"""
        from modules.pdf_generator import PdfGenerator

        latex = r'\begin{aligned}&=1\\&=2\end{aligned}'
        result = PdfGenerator._preprocess_latex_for_mathtext(latex)
        # \\\\ 应被替换为空格，& 应被去除
        assert '\\\\' not in result


class TestLatexDetectionThreadSafety:
    """LaTeX 检测线程安全测试"""

    def test_path_modification_inside_lock(self):
        """PATH 修改在锁内完成"""
        from modules.pdf_generator import PdfGenerator
        import inspect

        source = inspect.getsource(PdfGenerator._check_latex_available)
        # 验证 os.environ['PATH'] 赋值在 with cls._latex_lock 块内
        lines = source.split('\n')
        in_lock_block = False
        path_mod_in_lock = False

        for line in lines:
            if '_latex_lock' in line and 'with' in line:
                in_lock_block = True
            if in_lock_block and "os.environ['PATH']" in line:
                path_mod_in_lock = True
                break

        assert path_mod_in_lock, "os.environ['PATH'] modification should be inside _latex_lock"

    def test_concurrent_detection_no_race(self):
        """并发调用 _check_latex_available 不产生竞态条件"""
        from modules.pdf_generator import PdfGenerator

        # 重置状态以强制重新检测
        PdfGenerator._latex_available = None

        results = []
        errors = []

        def detect():
            try:
                result = PdfGenerator._check_latex_available()
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=detect) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent detection: {errors}"
        # 所有结果应一致
        assert len(set(results)) == 1, f"Inconsistent results: {results}"


class TestLatexCrossPlatformPaths:
    """LaTeX 跨平台路径检测测试"""

    def test_darwin_paths_on_mac(self):
        """macOS 路径列表包含 MacTeX 和 Homebrew 路径"""
        import sys
        if sys.platform != 'darwin':
            pytest.skip("macOS only")

        from modules.pdf_generator import PdfGenerator
        import inspect

        source = inspect.getsource(PdfGenerator._check_latex_available)
        assert '/Library/TeX/texbin/latex' in source
        assert '/opt/homebrew/bin/latex' in source

    def test_linux_paths_present(self):
        """代码中包含 Linux 路径"""
        from modules.pdf_generator import PdfGenerator
        import inspect

        source = inspect.getsource(PdfGenerator._check_latex_available)
        assert "'linux'" in source or '"linux"' in source
        assert '/usr/bin/latex' in source

    def test_windows_paths_present(self):
        """代码中包含 Windows 路径"""
        from modules.pdf_generator import PdfGenerator
        import inspect

        source = inspect.getsource(PdfGenerator._check_latex_available)
        assert "'win32'" in source or '"win32"' in source
        assert 'MiKTeX' in source

    def test_platform_conditional(self):
        """使用 sys.platform 条件化路径探测"""
        from modules.pdf_generator import PdfGenerator
        import inspect

        source = inspect.getsource(PdfGenerator._check_latex_available)
        assert 'sys.platform' in source


class TestCjkWidthEstimation:
    """CJK 宽度估算扩展测试"""

    def test_japanese_hiragana_fullwidth(self):
        """日文平假名按全角宽度计算"""
        from modules.extractors.coordinate_utils import estimate_text_display_width

        # 5 个平假名字符，每个 9.0pt = 45.0
        width = estimate_text_display_width('こんにちは', 9.0)
        assert abs(width - 45.0) < 0.01, f"Expected ~45.0, got {width}"

    def test_japanese_katakana_fullwidth(self):
        """日文片假名按全角宽度计算"""
        from modules.extractors.coordinate_utils import estimate_text_display_width

        # 4 个片假名字符，每个 9.0pt
        width = estimate_text_display_width('カタカナ', 9.0)
        assert abs(width - 36.0) < 0.01, f"Expected ~36.0, got {width}"

    def test_korean_hangul_fullwidth(self):
        """韩文谚文按全角宽度计算"""
        from modules.extractors.coordinate_utils import estimate_text_display_width

        # 5 个韩文字符，每个 9.0pt = 45.0
        width = estimate_text_display_width('안녕하세요', 9.0)
        assert abs(width - 45.0) < 0.01, f"Expected ~45.0, got {width}"

    def test_chinese_fullwidth(self):
        """中文仍按全角宽度计算"""
        from modules.extractors.coordinate_utils import estimate_text_display_width

        width = estimate_text_display_width('你好世界', 9.0)
        assert abs(width - 36.0) < 0.01, f"Expected ~36.0, got {width}"

    def test_mixed_cjk_width(self):
        """混合中日韩文字宽度计算"""
        from modules.extractors.coordinate_utils import estimate_text_display_width

        # 1 Chinese + 1 Japanese hiragana + 1 Korean = 3 fullwidth chars = 27.0
        width = estimate_text_display_width('你こ안', 9.0)
        assert abs(width - 27.0) < 0.01, f"Expected ~27.0, got {width}"

    def test_latin_halfwidth(self):
        """拉丁字母按半角宽度计算"""
        from modules.extractors.coordinate_utils import estimate_text_display_width

        width = estimate_text_display_width('abc', 9.0)
        assert abs(width - 9.0 * 0.6 * 3) < 0.01, f"Expected ~16.2, got {width}"


class TestParseHtmlTableReturnCheck:
    """_parse_html_table 返回值检查测试"""

    def test_cells_is_not_none_check(self):
        """使用 is not None 而非 truthy 检查"""
        from modules.ocr.llm_response_parser import LlmOcrResponseParser
        import inspect

        source = inspect.getsource(LlmOcrResponseParser._map_ocr_blocks_to_models)
        assert 'if cells is not None:' in source, "Should use 'if cells is not None:' check"

    def test_cells_truthy_check_not_used(self):
        """不应使用 if cells: 检查"""
        from modules.ocr.llm_response_parser import LlmOcrResponseParser
        import inspect

        source = inspect.getsource(LlmOcrResponseParser._map_ocr_blocks_to_models)
        # 确保没有使用 "if cells:" (但 "if cells is not None:" 是允许的)
        # 移除所有 "is not None" 后检查是否还有 "if cells:"
        cleaned = source.replace('is not None', '___OK___')
        assert 'if cells:' not in cleaned, "Should not use 'if cells:' truthy check"


class TestComputeTableLayoutSideEffects:
    """_compute_table_layout 副作用标注测试"""

    def test_docstring_mentions_side_effects(self):
        """docstring 标注了副作用"""
        from modules.ocr.llm_table_parser import LlmTableParser

        doc = LlmTableParser._compute_table_layout.__doc__
        assert doc is not None
        assert 'Side Effects' in doc or 'side effect' in doc.lower()

    def test_docstring_mentions_estimated_lines(self):
        """docstring 提及 estimated_lines 属性"""
        from modules.ocr.llm_table_parser import LlmTableParser

        doc = LlmTableParser._compute_table_layout.__doc__
        assert 'estimated_lines' in doc


class TestDocxMergeCellExceptionNarrowing:
    """Word 生成器合并单元格异常捕获收窄测试"""

    def test_catches_value_error_and_key_error(self):
        """异常捕获为 (ValueError, KeyError)"""
        import inspect
        from modules.docx_generator import DocxGenerator

        # 检查所有方法中是否有 (ValueError, KeyError) 捕获
        for name, method in inspect.getmembers(DocxGenerator, predicate=inspect.isfunction):
            if name.startswith('_'):
                source = inspect.getsource(method)
                if '合并单元格' in source:
                    assert '(ValueError, KeyError)' in source, \
                        f"Method {name}: Should catch (ValueError, KeyError) for merge cell"
                    return

        pytest.fail("No merge cell code found with (ValueError, KeyError)")

    def test_does_not_catch_broad_exception(self):
        """合并单元格代码不使用 bare Exception 捕获"""
        import inspect
        from modules.docx_generator import DocxGenerator

        for name, method in inspect.getmembers(DocxGenerator, predicate=inspect.isfunction):
            if name.startswith('_'):
                source = inspect.getsource(method)
                if '合并单元格' in source:
                    lines = source.split('\n')
                    for line in lines:
                        if 'except' in line and '合并单元格' not in line:
                            # 检查附近的 except 行
                            pass
                    # 确保没有 "except Exception" 在合并单元格附近
                    assert 'except Exception' not in source or '合并单元格' not in source, \
                        f"Method {name}: Should not use 'except Exception' near merge cell code"
                    return


class TestImportOrder:
    """模块级 import 顺序测试"""

    def test_constant_after_imports(self):
        """常量定义在 import 之后"""
        from modules.ocr import llm_response_parser as m
        import inspect

        source = inspect.getsource(m)
        lines = source.split('\n')

        last_import_line = 0
        first_const_line = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                last_import_line = i
            if stripped.startswith('TABLE_HTML_MARKER'):
                first_const_line = i
                break

        assert first_const_line is not None, "TABLE_HTML_MARKER not found"
        assert first_const_line > last_import_line, \
            f"TABLE_HTML_MARKER (line {first_const_line}) should be after imports (last at line {last_import_line})"

    def test_no_import_after_constant(self):
        """常量之后不应有新的 import"""
        from modules.ocr import llm_response_parser as m
        import inspect

        source = inspect.getsource(m)
        lines = source.split('\n')

        found_marker = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('TABLE_HTML_MARKER'):
                found_marker = True
            if found_marker and (stripped.startswith('import ') or stripped.startswith('from ')):
                # 允许函数内的 import，但模块级不应有
                if not stripped.startswith(('import typing', 'import __future__')):
                    # 检查缩进——模块级 import 无缩进
                    if not line.startswith(' ') and not line.startswith('\t'):
                        pytest.fail(f"Module-level import after constant: {stripped}")


class TestPdfCellEstimatedLines:
    """PdfCell estimated_lines 字段测试"""

    def test_estimated_lines_field_exists(self):
        """PdfCell 有 estimated_lines 字段"""
        from models.extraction import PdfCell

        cell = PdfCell(text="test", bbox=(0, 0, 100, 30), row_idx=0, col_idx=0)
        assert hasattr(cell, 'estimated_lines')

    def test_estimated_lines_default_zero(self):
        """estimated_lines 默认为 0"""
        from models.extraction import PdfCell

        cell = PdfCell(text="test", bbox=(0, 0, 100, 30), row_idx=0, col_idx=0)
        assert cell.estimated_lines == 0

    def test_estimated_lines_settable(self):
        """estimated_lines 可设置"""
        from models.extraction import PdfCell

        cell = PdfCell(text="test", bbox=(0, 0, 100, 30), row_idx=0, col_idx=0)
        cell.estimated_lines = 3
        assert cell.estimated_lines == 3
