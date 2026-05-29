#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR模块测试

测试OCR提取器的创建、配置和核心逻辑。
OCR引擎调用使用mock避免依赖PaddleOCR实际安装。
"""

import pytest
import os
from unittest.mock import patch, MagicMock, PropertyMock


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

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor.pipeline', new_callable=PropertyMock)
    def test_extract_from_pdf_basic(self, mock_pipeline_prop, mock_fitz,
                                     mock_exists, mock_makedirs):
        """测试基本PDF提取流程（mock）"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        # Mock PyMuPDF
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value.save = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        # Mock PP-StructureV3结果 — 文本区域
        mock_result = MagicMock()
        mock_result.res = {
            'layout_det_res': {
                'bboxes': [[10, 10, 200, 50]],
                'labels': ['text'],
            },
            'ocr_res': {
                'rec_texts': ['Hello World'],
                'dt_polys': [[[10, 10], [200, 10], [200, 50], [10, 50]]],
            },
        }

        mock_pipeline = MagicMock()
        mock_pipeline.predict.return_value = [mock_result]
        mock_pipeline_prop.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en')
        result = extractor.extract_from_pdf('test.pdf')

        assert isinstance(result, PdfExtraction)
        assert result.total_pages == 2
        assert len(result.pages) == 2
        assert len(result.pages[0].text_blocks) == 1
        assert result.pages[0].text_blocks[0].block_text == 'Hello World'

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor.pipeline', new_callable=PropertyMock)
    def test_extract_from_pdf_with_table(self, mock_pipeline_prop, mock_fitz,
                                          mock_exists, mock_makedirs):
        """测试提取包含表格的PDF"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        # Mock PyMuPDF
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value.save = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        # Mock PP-StructureV3结果 — 表格区域
        mock_result = MagicMock()
        mock_result.res = {
            'layout_det_res': {
                'bboxes': [[10, 10, 300, 200]],
                'labels': ['table'],
            },
            'ocr_res': {
                'rec_texts': [],
                'dt_polys': [],
            },
            'table_res_list': [
                {
                    'html': '<html><body><table>'
                            '<tr><td>A</td><td>B</td></tr>'
                            '<tr><td>1</td><td>2</td></tr>'
                            '</table></body></html>',
                }
            ],
        }

        mock_pipeline = MagicMock()
        mock_pipeline.predict.return_value = [mock_result]
        mock_pipeline_prop.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en')
        result = extractor.extract_from_pdf('test.pdf')

        assert isinstance(result, PdfExtraction)
        assert len(result.tables) == 1
        assert result.tables[0].page_num == 1
        assert len(result.tables[0].cells) == 2  # 2 rows
        assert result.tables[0].cells[0][0].text == 'A'

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor.pipeline', new_callable=PropertyMock)
    def test_extract_from_pdf_non_body_labels(self, mock_pipeline_prop, mock_fitz,
                                                mock_exists, mock_makedirs):
        """测试header/footer/page_number标记为非正文"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        # Mock PyMuPDF
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value.save = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        mock_result = MagicMock()
        mock_result.res = {
            'layout_det_res': {
                'bboxes': [[10, 10, 200, 30], [10, 40, 200, 100]],
                'labels': ['header', 'text'],
            },
            'ocr_res': {
                'rec_texts': ['Page Header', 'Body Text'],
                'dt_polys': [
                    [[10, 10], [200, 10], [200, 30], [10, 30]],
                    [[10, 40], [200, 40], [200, 100], [10, 100]],
                ],
            },
        }

        mock_pipeline = MagicMock()
        mock_pipeline.predict.return_value = [mock_result]
        mock_pipeline_prop.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en')
        result = extractor.extract_from_pdf('test.pdf')

        blocks = result.pages[0].text_blocks
        # header should be marked as non-body
        header_block = [b for b in blocks if b.block_text == 'Page Header'][0]
        body_block = [b for b in blocks if b.block_text == 'Body Text'][0]
        assert header_block.is_body_text is False
        assert body_block.is_body_text is True

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor.pipeline', new_callable=PropertyMock)
    def test_extract_from_pdf_specific_pages(self, mock_pipeline_prop, mock_fitz,
                                              mock_exists, mock_makedirs):
        """测试指定页码范围提取"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        # Mock PyMuPDF
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value.save = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        mock_result = MagicMock()
        mock_result.res = {
            'layout_det_res': {
                'bboxes': [[10, 10, 200, 50]],
                'labels': ['text'],
            },
            'ocr_res': {
                'rec_texts': ['Test'],
                'dt_polys': [[[10, 10], [200, 10], [200, 50], [10, 50]]],
            },
        }

        mock_pipeline = MagicMock()
        mock_pipeline.predict.return_value = [mock_result]
        mock_pipeline_prop.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en')
        result = extractor.extract_from_pdf('test.pdf', pages=[2, 3])

        assert isinstance(result, PdfExtraction)
        assert result.total_pages == 5
        assert len(result.pages) == 2  # only pages 2 and 3

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.paddle_extractor.fitz')
    @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor.pipeline', new_callable=PropertyMock)
    def test_extract_from_pdf_empty_page(self, mock_pipeline_prop, mock_fitz,
                                          mock_exists, mock_makedirs):
        """测试空页面"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        from models.extraction import PdfExtraction

        # Mock PyMuPDF
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value.save = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.open.return_value = mock_doc

        # Empty page - no layout result
        mock_result = MagicMock()
        mock_result.res = {}

        mock_pipeline = MagicMock()
        mock_pipeline.predict.return_value = [mock_result]
        mock_pipeline_prop.return_value = mock_pipeline

        extractor = PaddleOcrExtractor(lang='en')
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
        """测试 GPU 可用时使用 GPU"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        mock_instance = MagicMock()
        mock_ppv3.return_value = mock_instance

        extractor = PaddleOcrExtractor(lang='en', use_gpu=True)
        _ = extractor.pipeline

        # 应该使用 gpu:0
        mock_ppv3.assert_called_once()
        call_kwargs = mock_ppv3.call_args[1]
        assert call_kwargs['device'] == 'gpu:0'

    @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor._check_gpu_available', return_value=False)
    @patch('paddleocr.PPStructureV3')
    def test_pipeline_fallback_to_cpu(self, mock_ppv3, mock_check_gpu):
        """测试 GPU 不可用时回退到 CPU"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        mock_instance = MagicMock()
        mock_ppv3.return_value = mock_instance

        extractor = PaddleOcrExtractor(lang='en', use_gpu=True)
        _ = extractor.pipeline

        # 应该回退到 cpu
        mock_ppv3.assert_called_once()
        call_kwargs = mock_ppv3.call_args[1]
        assert call_kwargs['device'] == 'cpu'

    @patch('paddleocr.PPStructureV3', side_effect=ImportError("No module"))
    def test_pipeline_init_error(self, mock_ppv3):
        """测试 PaddleOCR 初始化失败时的异常处理"""
        from modules.ocr.paddle_extractor import PaddleOcrExtractor

        extractor = PaddleOcrExtractor(lang='en', use_gpu=False)
        with pytest.raises(RuntimeError, match="OCR 引擎初始化失败"):
            _ = extractor.pipeline


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
        assert parser.rows[0] == ['A', 'B']
        assert parser.rows[1] == ['1', '2']

    def test_parse_empty_table(self):
        """测试空表格解析"""
        from modules.ocr.paddle_extractor import _TableHtmlParser

        html = '<html><body><table></table></body></html>'

        parser = _TableHtmlParser()
        parser.feed(html)

        assert len(parser.rows) == 0