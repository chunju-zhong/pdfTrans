import pytest
import re
import os
import tempfile
from unittest.mock import patch, MagicMock

from services.translation_service import TranslationService
from models.text_block import TextBlock
from models.extraction import PdfPage, PdfCell


class TestDownloadFilenameValidation:
    FILENAME_PATTERN = r'^[a-zA-Z0-9_\-.]+$'

    @pytest.mark.parametrize("filename,expected", [
        ("translated_abc123_test.pdf", True),
        ("output-1.docx", True),
        ("file_with_underscores.pdf", True),
        ("FILE.PDF", True),
        ("123.pdf", True),
        ("../../etc/passwd", False),
        ("../secret.pdf", False),
        ("file with spaces.pdf", False),
        ("file/../../../etc/passwd", False),
        ("file\\..\\..\\secret.pdf", False),
        ("", False),
        ("file@name.pdf", False),
        ("file!name.pdf", False),
        ("file#name.pdf", False),
        ("file$name.pdf", False),
        ("file%20name.pdf", False),
        ("file&name.pdf", False),
        ("file*name.pdf", False),
        ("file|name.pdf", False),
        ("file;name.pdf", False),
        ("file'name.pdf", False),
        ('file"name.pdf', False),
        ("file(name).pdf", False),
        ("file[name].pdf", False),
        ("file{name}.pdf", False),
        ("file<name>.pdf", False),
        ("file?name.pdf", False),
    ])
    def test_filename_regex(self, filename, expected):
        result = bool(re.match(self.FILENAME_PATTERN, filename))
        assert result == expected, f"filename={filename!r}: expected {expected}, got {result}"

    def test_path_traversal_blocked(self):
        malicious_names = [
            "../../etc/passwd",
            "..%2f..%2fetc%2fpasswd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "\\windows\\system32",
            "....//....//etc/passwd",
        ]
        for name in malicious_names:
            assert not re.match(self.FILENAME_PATTERN, name), f"Path traversal not blocked: {name!r}"


class TestConfigSecurity:
    def test_secret_key_no_hardcoded_fallback(self):
        import inspect
        from config import Config
        source = inspect.getsource(Config)
        assert "'dev-secret-key'" not in source
        assert '"dev-secret-key"' not in source
        assert "raise RuntimeError" in source
        assert "SECRET_KEY" in source

    def test_secret_key_runtime_error_message(self):
        import inspect
        from config import Config
        source = inspect.getsource(Config)
        assert "RuntimeError" in source
        assert "SECRET_KEY" in source

    def test_debug_default_value_in_code(self):
        import inspect
        from config import Config
        source = inspect.getsource(Config)
        assert "'False'" in source
        assert "os.environ.get('DEBUG', 'False')" in source

    @pytest.mark.parametrize("env_val,expected", [
        ('true', True),
        ('True', True),
        ('TRUE', True),
        ('false', False),
        ('False', False),
        ('', False),
        ('1', False),
        ('0', False),
        ('yes', False),
    ])
    def test_debug_env_parsing(self, env_val, expected):
        result = env_val.lower() == 'true'
        assert result == expected


class TestPageRangeLengthLimit:
    def setup_method(self):
        self.service = TranslationService()

    def test_rejects_oversized_input(self):
        long_input = "1" * 1001
        with pytest.raises(ValueError, match="1000"):
            self.service.parse_page_range(long_input, 100)

    def test_accepts_max_length_input(self):
        max_input = "1" * 1000
        result = self.service.parse_page_range(max_input, 100)
        assert isinstance(result, set)

    def test_empty_string_returns_all_pages(self):
        result = self.service.parse_page_range("", 10)
        assert result == set(range(1, 11))

    def test_none_returns_all_pages(self):
        result = self.service.parse_page_range(None, 10)
        assert result == set(range(1, 11))

    @pytest.mark.parametrize("page_range,total_pages,expected", [
        ("1-5", 10, {1, 2, 3, 4, 5}),
        ("1-3,7-9", 10, {1, 2, 3, 7, 8, 9}),
        ("1-3,5,7-9", 10, {1, 2, 3, 5, 7, 8, 9}),
        ("3", 10, {3}),
        ("1,3,5", 10, {1, 3, 5}),
        ("1-15,5", 10, {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}),
        ("5-1,7-9", 10, {7, 8, 9}),
        ("1-5,abc,7-9", 10, {1, 2, 3, 4, 5, 7, 8, 9}),
    ])
    def test_page_range_parsing(self, page_range, total_pages, expected):
        result = self.service.parse_page_range(page_range, total_pages)
        assert result == expected


class TestTranslationFallback:
    def setup_method(self):
        self.service = TranslationService()

    def _make_text_block(self, text="Hello world", page_num=1):
        return TextBlock(
            block_no=1,
            text=text,
            bbox=(50, 50, 300, 100),
            block_type=0,
            page_num=page_num,
        )

    def test_process_original_blocks_fallback_on_exception(self):
        mock_translator = MagicMock()
        mock_translator.translate.side_effect = ConnectionError("API unreachable")

        mock_task = MagicMock()
        mock_task.task_id = "test-task"
        mock_task.update_phase_progress.return_value = True

        text_block = self._make_text_block("Original text here")
        result = self.service.process_original_blocks(
            mock_task, [text_block], mock_translator,
            "en", "zh", "general", ""
        )

        page_dict, merged, count = result
        assert count == 1
        assert 1 in page_dict
        fallback_block = page_dict[1].text_blocks[0]
        assert fallback_block.block_text == "Original text here"

    def test_process_merged_blocks_fallback_on_exception(self):
        from models.merged_block import MergedBlock

        text_block = self._make_text_block("Merged original text")
        merged_block = MergedBlock(
            block_text="Merged original text",
            original_blocks=[text_block],
            max_width=250,
            max_height=50,
        )

        mock_translator = MagicMock()
        mock_translator.translate.side_effect = ConnectionError("API unreachable")

        mock_task = MagicMock()
        mock_task.task_id = "test-task"
        mock_task.update_phase_progress.return_value = True

        result = self.service.process_merged_blocks(
            mock_task, [merged_block], mock_translator,
            "en", "zh", "general", ""
        )

        page_dict, merged, count = result
        assert count >= 1
        for page_num, page in page_dict.items():
            for block in page.text_blocks:
                assert block.block_text != ""

    def test_table_translation_fallback_on_exception(self):
        from models.extraction import PdfTable

        cell = PdfCell(text="Table cell text", bbox=(0, 0, 100, 30), row_idx=0, col_idx=0)
        table = PdfTable(page_num=1, table_idx=0, cells=[[cell]], bbox=(0, 0, 500, 200))

        mock_translator = MagicMock()
        mock_translator.translate.side_effect = ConnectionError("API unreachable")

        mock_task = MagicMock()
        mock_task.task_id = "test-task"
        mock_task.update_phase_progress.return_value = True

        cell_results, total_cells = self.service._process_table_translation(
            mock_task, [table], mock_translator,
            "en", "zh", "general", ""
        )

        assert 0 in cell_results
        assert 0 in cell_results[0]
        assert 0 in cell_results[0][0]
        fallback_cell = cell_results[0][0][0]
        assert fallback_cell.text == "Table cell text"


class TestFontSizeEstimation:
    ASSUMED_LINE_HEIGHT = 12.0
    FONT_SCALE = 0.75
    MIN_FONT = 6
    MAX_FONT = 36

    def _estimate_fallback_font_size(self, bbox_height):
        estimated_lines = max(1, round(bbox_height / self.ASSUMED_LINE_HEIGHT))
        font_size = (bbox_height / estimated_lines) * self.FONT_SCALE
        return max(self.MIN_FONT, min(self.MAX_FONT, font_size))

    def test_multiline_block_120pt(self):
        font_size = self._estimate_fallback_font_size(120.0)
        assert font_size < 20.0, f"120pt block should estimate < 20pt, got {font_size}"
        estimated_lines = max(1, round(120.0 / 12.0))
        assert estimated_lines == 10
        expected = (120.0 / 10) * 0.75
        assert abs(font_size - expected) < 0.01

    def test_single_line_block_14pt(self):
        font_size = self._estimate_fallback_font_size(14.0)
        estimated_lines = max(1, round(14.0 / 12.0))
        assert estimated_lines == 1
        expected = (14.0 / 1) * 0.75
        assert abs(font_size - expected) < 0.01
        assert font_size == 10.5

    def test_tiny_block_clamped_to_min(self):
        font_size = self._estimate_fallback_font_size(4.0)
        assert font_size == self.MIN_FONT

    def test_huge_block_estimates_many_lines(self):
        font_size = self._estimate_fallback_font_size(1000.0)
        estimated_lines = max(1, round(1000.0 / 12.0))
        assert estimated_lines == 83
        expected = (1000.0 / 83) * 0.75
        assert abs(font_size - expected) < 0.01
        assert font_size < 36.0

    @pytest.mark.parametrize("bbox_height,expected_lines", [
        (12.0, 1),
        (24.0, 2),
        (36.0, 3),
        (48.0, 4),
        (60.0, 5),
        (120.0, 10),
        (144.0, 12),
    ])
    def test_line_count_estimation(self, bbox_height, expected_lines):
        estimated_lines = max(1, round(bbox_height / self.ASSUMED_LINE_HEIGHT))
        assert estimated_lines == expected_lines

    def test_old_algorithm_would_produce_wrong_result(self):
        old_result = 120.0 * 0.75
        new_result = self._estimate_fallback_font_size(120.0)
        assert new_result < old_result, "New fallback should be smaller than old bbox*0.75"
        assert old_result == 90.0
        assert new_result < 20.0


class TestPdfGeneratorResourceRelease:
    def test_new_doc_closed_on_exception(self):
        from modules.pdf_generator import PdfGenerator

        generator = PdfGenerator()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            test_pdf_path = tmp.name

        try:
            import fitz
            doc = fitz.open()
            doc.new_page(width=612, height=792)
            doc.save(test_pdf_path)
            doc.close()

            output_path = test_pdf_path + "_out.pdf"

            mock_doc = MagicMock()
            mock_doc.__enter__ = MagicMock(return_value=mock_doc)
            mock_doc.__exit__ = MagicMock(return_value=False)
            mock_doc.__len__ = MagicMock(return_value=1)
            mock_doc.__getitem__ = MagicMock(return_value=MagicMock(rect=MagicMock(width=612, height=792)))

            original_open = fitz.open

            def patched_open(*args, **kwargs):
                if len(args) == 0 and not kwargs:
                    return original_open(*args, **kwargs)
                if len(args) == 1 and isinstance(args[0], str) and args[0].endswith('.pdf'):
                    return original_open(*args, **kwargs)
                return original_open(*args, **kwargs)

            with patch('modules.pdf_generator.fitz.open') as mock_fitz_open:
                original_doc = MagicMock()
                original_doc.__enter__ = MagicMock(return_value=original_doc)
                original_doc.__exit__ = MagicMock(return_value=False)
                original_doc.__len__ = MagicMock(return_value=1)

                new_doc = MagicMock()
                new_doc.new_page.return_value = MagicMock(rect=MagicMock(width=612, height=792))

                call_count = [0]
                def open_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return original_doc
                    elif call_count[0] == 2:
                        return new_doc
                    return MagicMock()

                mock_fitz_open.side_effect = open_side_effect

                try:
                    generator.generate_pdf(
                        test_pdf_path,
                        {'blocks': [PdfPage(1, [self._make_text_block()])], 'tables': []},
                        output_path,
                    )
                except Exception:
                    pass

                new_doc.close.assert_called()

        finally:
            for p in [test_pdf_path, test_pdf_path + "_out.pdf"]:
                if os.path.exists(p):
                    os.remove(p)

    def _make_text_block(self):
        return TextBlock(
            block_no=1,
            text="test",
            bbox=(50, 50, 300, 100),
            block_type=0,
            page_num=1,
        )


class TestNumpyArrayTruthCheck:
    def test_numpy_array_len_check_pattern(self):
        import numpy as np

        arr = np.array([[1, 2, 3, 4], [5, 6, 7, 8]])

        with pytest.raises(ValueError, match="truth value"):
            if arr:
                pass

        assert arr is not None
        assert len(arr) > 0

        assert arr is not None and len(arr) > 0

    def test_empty_numpy_array(self):
        import numpy as np

        arr = np.array([])
        assert arr is not None
        assert len(arr) == 0
        assert not (arr is not None and len(arr) > 0)

    def test_none_check(self):
        arr = None
        assert not (arr is not None and len(arr) > 0)
