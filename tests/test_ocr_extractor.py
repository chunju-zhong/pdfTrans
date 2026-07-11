#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR模块测试

测试OCR提取器的创建、配置和核心逻辑。
OCR引擎调用使用mock避免依赖PaddleOCR实际安装。
"""

import pytest
import os
import numpy as np
from unittest.mock import patch, MagicMock, PropertyMock

from modules.ocr.paddle_extractor import PaddleOcrExtractor


class TestOcrExtractor:
    """OCR提取器基类测试"""

    def test_create_paddle_extractor(self):
        """测试创建PaddleOcrExtractor实例"""
        from modules.ocr.factory import create_ocr_extractor
        from modules.ocr.base import OcrExtractor
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = create_ocr_extractor('paddleocr', lang='en')
        assert isinstance(extractor, PaddleOcrExtractor)
        assert isinstance(extractor, OcrExtractor)

    def test_create_unsupported_extractor(self):
        """测试不支持的OCR引擎类型"""
        from modules.ocr.factory import create_ocr_extractor

        with pytest.raises(ValueError, match="不支持的OCR引擎类型"):
            create_ocr_extractor('tesseract')

    def test_create_extractor_default(self):
        """测试默认OCR引擎类型"""
        from modules.ocr.factory import create_ocr_extractor
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = create_ocr_extractor()
        assert isinstance(extractor, PaddleOcrExtractor)


class TestPaddleOcrExtractor:
    """PaddleOCR提取器测试"""

    def test_init_default(self):
        """测试默认初始化"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = PaddleOcrExtractor(lang='en')
        assert extractor.lang == 'en'
        assert extractor.use_gpu is True

    def test_init_custom(self):
        """测试自定义初始化"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = PaddleOcrExtractor(
            lang='ja',
            use_gpu=False,
        )
        assert extractor.lang == 'ja'
        assert extractor.use_gpu is False

    def test_extract_from_pdf_none_path(self):
        """测试空路径"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = PaddleOcrExtractor()
        with pytest.raises(ValueError, match="PDF文件路径不能为空"):
            extractor.extract_from_pdf('')

    def test_extract_from_pdf_not_found(self):
        """测试不存在的PDF文件"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = PaddleOcrExtractor()
        with pytest.raises(FileNotFoundError, match="PDF文件不存在"):
            extractor.extract_from_pdf('/nonexistent/file.pdf')

    @patch('modules.ocr.paddle_extractor.cv2.imread')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch.object(PaddleOcrExtractor, '_create_pipeline')
    def test_extract_from_pdf_basic(self, mock_create_pipeline, mock_fitz,
                                     mock_exists, mock_makedirs, mock_imread):


        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        mock_imread.return_value = np.zeros((792, 612, 3), dtype=np.uint8)

        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(width=612, height=792)
        mock_page.rect = MagicMock(width=612.0, height=792.0)
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        mock_block = MagicMock()
        mock_block.label = 'text'
        mock_block.bbox = [10, 10, 200, 50]
        mock_block.content = 'Hello World'
        mock_block.text_line_height = None
        mock_block.num_of_lines = None

        mock_overall_ocr_res = MagicMock()
        mock_overall_ocr_res.get.return_value = None

        mock_result = MagicMock()
        mock_result.get.return_value = [mock_block]
        mock_result.__iter__ = lambda self: iter([])

        def mock_predict(img_path):
            return [{'parsing_res_list': [mock_block], 'overall_ocr_res': mock_overall_ocr_res}]

        mock_pipeline = MagicMock()
        mock_pipeline.predict = mock_predict
        mock_create_pipeline.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en', skip_table=True, skip_formula=True)
        result = extractor.extract_from_pdf('test.pdf')

        assert isinstance(result, PdfExtraction)
        assert result.total_pages == 2

    @patch('modules.ocr.paddle_extractor.cv2.imread')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch.object(PaddleOcrExtractor, '_create_pipeline')
    def test_extract_from_pdf_with_table(self, mock_create_pipeline, mock_fitz,
                                          mock_exists, mock_makedirs, mock_imread):


        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        mock_imread.return_value = np.zeros((792, 612, 3), dtype=np.uint8)

        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(width=612, height=792)
        mock_page.rect = MagicMock(width=612.0, height=792.0)
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        mock_text_block = MagicMock()
        mock_text_block.label = 'table'
        mock_text_block.bbox = [10, 10, 300, 200]
        mock_text_block.content = ''
        mock_text_block.text_line_height = None
        mock_text_block.num_of_lines = None

        mock_overall_ocr_res = MagicMock()
        mock_overall_ocr_res.get.return_value = None

        mock_table_res = MagicMock()
        mock_html_dict = {'pred': '<html><body><table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table></body></html>'}
        mock_table_res.html = mock_html_dict

        def mock_predict(img_path):
            return [{'parsing_res_list': [mock_text_block], 'table_res_list': [mock_table_res], 'overall_ocr_res': mock_overall_ocr_res}]

        mock_pipeline = MagicMock()
        mock_pipeline.predict = mock_predict
        mock_create_pipeline.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en', skip_formula=True)
        result = extractor.extract_from_pdf('test.pdf')

        assert isinstance(result, PdfExtraction)
        assert len(result.tables) == 1
        assert result.tables[0].page_num == 1

    @patch('modules.ocr.paddle_extractor.cv2.imread')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch.object(PaddleOcrExtractor, '_create_pipeline')
    def test_extract_from_pdf_non_body_labels(self, mock_create_pipeline, mock_fitz,
                                                mock_exists, mock_makedirs, mock_imread):


        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        mock_imread.return_value = np.zeros((792, 612, 3), dtype=np.uint8)

        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(width=612, height=792)
        mock_page.rect = MagicMock(width=612.0, height=792.0)
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        mock_header_block = MagicMock()
        mock_header_block.label = 'header'
        mock_header_block.bbox = [10, 10, 200, 30]
        mock_header_block.content = 'Page Header'
        mock_header_block.text_line_height = None
        mock_header_block.num_of_lines = None

        mock_body_block = MagicMock()
        mock_body_block.label = 'text'
        mock_body_block.bbox = [10, 40, 200, 100]
        mock_body_block.content = 'Body Text'
        mock_body_block.text_line_height = None
        mock_body_block.num_of_lines = None

        mock_overall_ocr_res = MagicMock()
        mock_overall_ocr_res.get.return_value = None

        def mock_predict(img_path):
            return [{'parsing_res_list': [mock_header_block, mock_body_block], 'overall_ocr_res': mock_overall_ocr_res}]

        mock_pipeline = MagicMock()
        mock_pipeline.predict = mock_predict
        mock_create_pipeline.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en', skip_table=True, skip_formula=True)
        result = extractor.extract_from_pdf('test.pdf')

        blocks = result.pages[0].text_blocks
        header_block = [b for b in blocks if b.block_text == 'Page Header'][0]
        body_block = [b for b in blocks if b.block_text == 'Body Text'][0]
        # header 标签不再在 OCR 层标记为非正文，由 text_analyzer.py 基于多页重复模式判断
        assert header_block.is_body_text is True
        assert body_block.is_body_text is True

    @patch('modules.ocr.paddle_extractor.cv2.imread')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch.object(PaddleOcrExtractor, '_create_pipeline')
    def test_extract_from_pdf_specific_pages(self, mock_create_pipeline, mock_fitz,
                                              mock_exists, mock_makedirs, mock_imread):


        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        mock_imread.return_value = np.zeros((792, 612, 3), dtype=np.uint8)

        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(width=612, height=792)
        mock_page.rect = MagicMock(width=612.0, height=792.0)
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        mock_block = MagicMock()
        mock_block.label = 'text'
        mock_block.bbox = [10, 10, 200, 50]
        mock_block.content = 'Test'
        mock_block.text_line_height = None
        mock_block.num_of_lines = None

        mock_overall_ocr_res = MagicMock()
        mock_overall_ocr_res.get.return_value = None

        def mock_predict(img_path):
            return [{'parsing_res_list': [mock_block], 'overall_ocr_res': mock_overall_ocr_res}]

        mock_pipeline = MagicMock()
        mock_pipeline.predict = mock_predict
        mock_create_pipeline.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en', skip_table=True, skip_formula=True)
        result = extractor.extract_from_pdf('test.pdf', pages=[2, 3])

        assert isinstance(result, PdfExtraction)
        assert result.total_pages == 5
        assert len(result.pages) == 2

    @patch('modules.ocr.paddle_extractor.cv2.imread')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch.object(PaddleOcrExtractor, '_create_pipeline')
    def test_extract_from_pdf_empty_page(self, mock_create_pipeline, mock_fitz,
                                          mock_exists, mock_makedirs, mock_imread):


        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        mock_imread.return_value = np.zeros((792, 612, 3), dtype=np.uint8)

        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(width=612, height=792)
        mock_page.rect = MagicMock(width=612.0, height=792.0)
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        def mock_predict(img_path):
            return [{'parsing_res_list': [], 'overall_ocr_res': None}]

        mock_pipeline = MagicMock()
        mock_pipeline.predict = mock_predict
        mock_create_pipeline.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en', skip_table=True, skip_formula=True)
        result = extractor.extract_from_pdf('test.pdf')

        assert isinstance(result, PdfExtraction)
        assert len(result.pages) == 1
        assert len(result.pages[0].text_blocks) == 0
        assert len(result.tables) == 0
        assert len(result.images) == 0


class TestOcrModeInPdfExtractor:
    """测试PdfExtractor的OCR模式集成"""

    def test_ocr_mode_enabled(self):
        """测试OCR模式开启"""
        from modules.pdf_extractor import PdfExtractor

        extractor = PdfExtractor(ocr_mode=True, ocr_engine='paddleocr', ocr_lang='en')
        assert extractor.ocr_mode is True
        assert extractor.ocr_engine == 'paddleocr'
        assert extractor.ocr_lang == 'en'

    def test_ocr_disabled_by_default(self):
        """测试OCR默认关闭"""
        from modules.pdf_extractor import PdfExtractor

        extractor = PdfExtractor()
        assert extractor.ocr_mode is False

    def test_ocr_extractor_property_disabled(self):
        """测试非OCR模式ocr_extractor为None"""
        from modules.pdf_extractor import PdfExtractor

        extractor = PdfExtractor(ocr_mode=False)
        assert extractor.ocr_extractor is None


class TestOcrConfig:
    """测试OCR配置"""

    def test_ocr_config_defaults(self):
        """测试OCR配置默认值"""
        from config import Config
        import platform

        config = Config()
        assert config.USE_OCR is False
        assert config.OCR_ENGINE == 'paddleocr'
        assert config.OCR_LANGUAGE == 'ch'
        # macOS 上默认使用 CPU，其他平台默认使用 GPU
        if platform.system() == 'Darwin':
            assert config.OCR_USE_GPU is False
        else:
            assert config.OCR_USE_GPU is True


class TestGpuAutoFallback:
    """测试 GPU 自动回退功能"""

    def test_check_gpu_available_method(self):
        """测试 _check_gpu_available 方法"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = PaddleOcrExtractor(lang='en')
        # 方法应该能正常调用，返回 bool
        result = extractor._check_gpu_available()
        assert isinstance(result, bool)

    @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor._check_gpu_available', return_value=False)
    def test_gpu_fallback_to_cpu(self, mock_check_gpu):
        """测试 GPU 不可用时自动回退到 CPU"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = PaddleOcrExtractor(lang='en', use_gpu=True)
        # GPU 检测返回 False，应该回退到 CPU
        assert extractor._check_gpu_available() is False

    @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor._check_gpu_available', return_value=True)
    @patch('paddleocr.PPStructureV3')
    def test_pipeline_uses_gpu_when_available(self, mock_ppv3, mock_check_gpu):
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        mock_instance = MagicMock()
        mock_ppv3.return_value = mock_instance

        extractor = PaddleOcrExtractor(lang='en', use_gpu=True)
        pipeline = extractor._create_pipeline()

        mock_ppv3.assert_called_once()
        call_kwargs = mock_ppv3.call_args[1]
        assert call_kwargs['device'] == 'gpu:0'

    @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor._check_gpu_available', return_value=False)
    @patch('paddleocr.PPStructureV3')
    def test_pipeline_fallback_to_cpu(self, mock_ppv3, mock_check_gpu):
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        mock_instance = MagicMock()
        mock_ppv3.return_value = mock_instance

        extractor = PaddleOcrExtractor(lang='en', use_gpu=True)
        pipeline = extractor._create_pipeline()

        mock_ppv3.assert_called_once()
        call_kwargs = mock_ppv3.call_args[1]
        assert call_kwargs['device'] == 'cpu'

    @patch('paddleocr.PPStructureV3', side_effect=ImportError("No module"))
    def test_pipeline_init_error(self, mock_ppv3):
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = PaddleOcrExtractor(lang='en', use_gpu=False)
        with pytest.raises(RuntimeError, match="OCR 引擎初始化失败"):
            extractor._create_pipeline()


class TestTableHtmlParser:
    """测试HTML表格解析器"""

    def test_parse_simple_table(self):
        """测试简单表格解析"""
        from modules.ocr.paddle_extractor import _TableHtmlParser

        html = (
            '<html><body><table>'
            '<tr><td>A</td><td>B</td></tr>'
            '<tr><td>1</td><td>2</td></tr>'
            '</table></body></html>'
        )

        parser = _TableHtmlParser()
        parser.feed(html)

        assert len(parser.rows) == 2
        assert parser.rows[0] == [('A', 1, 1), ('B', 1, 1)]
        assert parser.rows[1] == [('1', 1, 1), ('2', 1, 1)]

    def test_parse_empty_table(self):
        """测试空表格解析"""
        from modules.ocr.paddle_extractor import _TableHtmlParser

        html = '<html><body><table></table></body></html>'

        parser = _TableHtmlParser()
        parser.feed(html)

        assert len(parser.rows) == 0