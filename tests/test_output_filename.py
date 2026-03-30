"""
测试输出文件名功能

测试 -o 参数指定的输出文件名是否正确应用于各种输出格式
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock, call, create_autospec

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.translation_service import TranslationService
from modules.pdf_generator import PdfGenerator
from modules.docx_generator import DocxGenerator


class TestOutputFilename(unittest.TestCase):
    """测试输出文件名功能"""

    def setUp(self):
        """测试前准备"""
        self.service = TranslationService()
        self.task = Mock()
        self.task.task_id = "test_task_id"
        self.task.update_phase_progress = Mock(return_value=True)
        self.task.add_warning = Mock()

    @patch('services.translation_service.PdfGenerator')
    @patch('services.translation_service.os.path.join')
    def test_generate_pdf_output_with_custom_filename(self, mock_join, MockPdfGenerator):
        """测试 PDF 输出使用自定义文件名"""
        mock_generator = Mock()
        MockPdfGenerator.return_value = mock_generator
        mock_join.return_value = "/output/custom_output.pdf"
        
        result = self.service.generate_pdf_output(
            task=self.task,
            input_filepath="/input/test.pdf",
            unique_id="abc123",
            filename="test.pdf",
            translated_content={},
            target_lang="zh",
            output_path="/output",
            output_filename="custom_output.pdf"
        )
        
        self.assertEqual(result, "custom_output.pdf")
        mock_generator.generate_pdf.assert_called_once()

    @patch('services.translation_service.PdfGenerator')
    def test_generate_pdf_output_without_custom_filename(self, MockPdfGenerator):
        """测试 PDF 输出使用自动生成文件名"""
        mock_generator = Mock()
        MockPdfGenerator.return_value = mock_generator
        
        result = self.service.generate_pdf_output(
            task=self.task,
            input_filepath="/input/test.pdf",
            unique_id="abc123",
            filename="test.pdf",
            translated_content={},
            target_lang="zh",
            output_path="/output",
            output_filename=None
        )
        
        self.assertEqual(result, "translated_abc123_test.pdf")

    @patch('services.translation_service.DocxGenerator')
    @patch('services.translation_service.os.path.join')
    def test_generate_docx_output_with_custom_filename(self, mock_join, MockDocxGenerator):
        """测试 DOCX 输出使用自定义文件名"""
        mock_generator = Mock()
        MockDocxGenerator.return_value = mock_generator
        mock_join.return_value = "/output/custom_output.docx"
        
        result = self.service.generate_docx_output(
            task=self.task,
            unique_id="abc123",
            filename="test.pdf",
            translated_content={},
            extracted_images=[],
            target_lang="zh",
            output_path="/output",
            output_filename="custom_output.docx"
        )
        
        self.assertEqual(result, "custom_output.docx")
        mock_generator.generate_docx.assert_called_once()

    @patch('services.translation_service.DocxGenerator')
    def test_generate_docx_output_without_custom_filename(self, MockDocxGenerator):
        """测试 DOCX 输出使用自动生成文件名"""
        mock_generator = Mock()
        MockDocxGenerator.return_value = mock_generator
        
        result = self.service.generate_docx_output(
            task=self.task,
            unique_id="abc123",
            filename="test.pdf",
            translated_content={},
            extracted_images=[],
            target_lang="zh",
            output_path="/output",
            output_filename=None
        )
        
        self.assertEqual(result, "translated_abc123_test.docx")

    @patch('services.translation_service.create_zip')
    @patch('services.translation_service.os.path.join')
    def test_generate_single_zip_with_custom_filename(self, mock_join, mock_create_zip):
        """测试单个 Markdown 压缩使用自定义文件名"""
        mock_join.return_value = "/output/custom_output.zip"
        
        result = self.service._generate_single_zip(
            task=self.task,
            unique_id="abc123",
            filename="test.pdf",
            md_filepath="/tmp/translated_test.md",
            output_path="/output",
            output_filename="custom_output.zip",
            tmp_dir="/tmp"
        )
        
        self.assertEqual(result, "custom_output.zip")

    @patch('services.translation_service.create_zip')
    def test_generate_single_zip_without_custom_filename(self, mock_create_zip):
        """测试单个 Markdown 压缩使用自动生成文件名"""
        result = self.service._generate_single_zip(
            task=self.task,
            unique_id="abc123",
            filename="test.pdf",
            md_filepath="/tmp/translated_test.md",
            output_path="/output",
            output_filename=None,
            tmp_dir="/tmp"
        )
        
        self.assertEqual(result, "translated_abc123_test.zip")


class TestOutputFilenameIntegration(unittest.TestCase):
    """集成测试：测试输出文件名在整个流程中的传递"""

    def setUp(self):
        """测试前准备"""
        self.service = TranslationService()
        self.task = Mock()
        self.task.task_id = "test_task_id"
        self.task.update_phase_progress = Mock(return_value=True)
        self.task.add_warning = Mock()
        self.task.set_status = Mock()
        self.task.is_canceled = Mock(return_value=False)
        self.task.set_result = Mock()
        self.task.add_attachment = Mock()

    @patch.object(TranslationService, 'generate_markdown_output')
    @patch.object(TranslationService, 'translate_tables')
    @patch.object(TranslationService, '_translate_content')
    @patch.object(TranslationService, '_create_translators')
    @patch.object(TranslationService, 'extract_pdf_content')
    def test_process_translation_sync_passes_output_filename(
        self, mock_extract, mock_create_translators, mock_translate_content,
        mock_translate_tables, mock_md_output
    ):
        """测试 process_translation_sync 正确传递 output_filename 参数"""
        mock_extract.return_value = ([], [], [], [])
        mock_create_translators.return_value = (Mock(), Mock())
        mock_translate_content.return_value = {'blocks': [], 'tables': []}
        mock_translate_tables.return_value = []
        mock_md_output.return_value = "custom_output.zip"
        
        result = self.service.process_translation_sync(
            task=self.task,
            input_filepath="/input/test.pdf",
            source_lang="en",
            target_lang="zh",
            translator_type="aiping",
            unique_id="abc123",
            filename="test.pdf",
            output_format="markdown",
            output_path="/output",
            output_filename="custom_output.zip",
            tmp_dir="/tmp"
        )
        
        mock_md_output.assert_called_once()
        args = mock_md_output.call_args[0]
        self.assertEqual(args[10], "custom_output.zip")

    @patch.object(TranslationService, 'generate_pdf_output')
    def test_generate_output_files_passes_output_filename_to_pdf(self, mock_pdf_output):
        """测试 generate_output_files 正确传递 output_filename 到 PDF"""
        mock_pdf_output.return_value = "custom_output.pdf"
        
        result = self.service.generate_output_files(
            task=self.task,
            input_filepath="/input/test.pdf",
            unique_id="abc123",
            filename="test.pdf",
            output_format="pdf",
            translated_content={},
            extracted_images=[],
            target_lang="zh",
            translator_type="aiping",
            chapters=None,
            chapter_split=False,
            output_path="/output",
            output_filename="custom_output.pdf",
            tmp_dir="/tmp"
        )
        
        mock_pdf_output.assert_called_once()
        args = mock_pdf_output.call_args[0]
        self.assertEqual(args[7], "custom_output.pdf")

    @patch.object(TranslationService, 'generate_docx_output')
    def test_generate_output_files_passes_output_filename_to_docx(self, mock_docx_output):
        """测试 generate_output_files 正确传递 output_filename 到 DOCX"""
        mock_docx_output.return_value = "custom_output.docx"
        
        result = self.service.generate_output_files(
            task=self.task,
            input_filepath="/input/test.pdf",
            unique_id="abc123",
            filename="test.pdf",
            output_format="docx",
            translated_content={},
            extracted_images=[],
            target_lang="zh",
            translator_type="aiping",
            chapters=None,
            chapter_split=False,
            output_path="/output",
            output_filename="custom_output.docx",
            tmp_dir="/tmp"
        )
        
        mock_docx_output.assert_called_once()
        args = mock_docx_output.call_args[0]
        self.assertEqual(args[7], "custom_output.docx")


class TestGlossaryOutputFilename(unittest.TestCase):
    """测试术语提取输出文件名"""

    def test_glossary_handler_with_custom_output(self):
        """测试术语提取使用自定义输出文件名"""
        from cli.glossary_command import glossary_handler
        
        args = Mock()
        args.input = "/input/test.pdf"
        args.output = "/output/custom_glossary.txt"
        args.source = "en"
        args.target = "zh"
        args.translator = "aiping"
        args.pages = "1-10"
        args.doc_type = "AI技术"
        args.verbose = False
        
        with patch('cli.glossary_command.os.path.exists', return_value=True):
            with patch('cli.glossary_command.allowed_file', return_value=True):
                with patch('cli.glossary_command.glossary_service') as mock_service:
                    with patch('cli.glossary_command.os.makedirs'):
                        with patch('builtins.open', create=True) as mock_open:
                            mock_service.extract_glossary_sync.return_value = "term1: 术语1\nterm2: 术语2"
                            
                            glossary_handler(args)
                            
                            mock_open.assert_called_once_with("/output/custom_glossary.txt", 'w', encoding='utf-8')

    def test_glossary_handler_without_custom_output(self):
        """测试术语提取使用自动生成文件名"""
        from cli.glossary_command import glossary_handler
        
        args = Mock()
        args.input = "/input/test.pdf"
        args.output = None
        args.source = "en"
        args.target = "zh"
        args.translator = "aiping"
        args.pages = None
        args.doc_type = "AI技术"
        args.verbose = False
        
        with patch('cli.glossary_command.os.path.exists', return_value=True):
            with patch('cli.glossary_command.allowed_file', return_value=True):
                with patch('cli.glossary_command.glossary_service') as mock_service:
                    with patch('cli.glossary_command.os.makedirs'):
                        with patch('builtins.open', create=True) as mock_open:
                            mock_service.extract_glossary_sync.return_value = "term1: 术语1"
                            
                            glossary_handler(args)
                            
                            mock_open.assert_called_once()
                            call_args = mock_open.call_args[0]
                            self.assertIn("glossary_test.txt", call_args[0])


class TestTranslateCommandOutputFilename(unittest.TestCase):
    """测试 translate 命令输出文件名传递"""

    def test_translate_handler_passes_output_filename(self):
        """测试 translate_handler 正确传递 output_filename"""
        from cli.translate_command import translate_handler
        
        args = Mock()
        args.input = "/input/test.pdf"
        args.output = "/output/custom_output.pdf"
        args.source = "en"
        args.target = "zh"
        args.translator = "aiping"
        args.pages = "1-5"
        args.format = "pdf"
        args.glossary = None
        args.doc_type = "AI技术"
        args.semantic_merge = False
        args.llm_merge = False
        args.chapter_split = False
        args.verbose = False
        
        with patch('cli.translate_command.os.path.exists', return_value=True):
            with patch('cli.translate_command.allowed_file', return_value=True):
                with patch('cli.translate_command.translation_service') as mock_service:
                    with patch('cli.translate_command.os.makedirs'):
                        with patch('cli.translate_command.task_service') as mock_task_service:
                            mock_task = Mock()
                            mock_task.task_id = "test_id"
                            mock_task.warnings = []
                            mock_task_service.create_task.return_value = mock_task
                            mock_service.process_translation_sync.return_value = "custom_output.pdf"
                            
                            translate_handler(args)
                            
                            mock_service.process_translation_sync.assert_called_once()
                            args, kwargs = mock_service.process_translation_sync.call_args
                            self.assertEqual(kwargs.get('output_filename'), "custom_output.pdf")

    def test_translate_handler_passes_output_filename_for_markdown(self):
        """测试 translate_handler 正确传递 output_filename 到 Markdown"""
        from cli.translate_command import translate_handler
        
        args = Mock()
        args.input = "/input/test.pdf"
        args.output = "/output/custom_output.zip"
        args.source = "en"
        args.target = "zh"
        args.translator = "aiping"
        args.pages = "1-5"
        args.format = "markdown"
        args.glossary = None
        args.doc_type = "AI技术"
        args.semantic_merge = True
        args.llm_merge = True
        args.chapter_split = True
        args.verbose = False
        
        with patch('cli.translate_command.os.path.exists', return_value=True):
            with patch('cli.translate_command.allowed_file', return_value=True):
                with patch('cli.translate_command.translation_service') as mock_service:
                    with patch('cli.translate_command.os.makedirs'):
                        with patch('cli.translate_command.task_service') as mock_task_service:
                            mock_task = Mock()
                            mock_task.task_id = "test_id"
                            mock_task.warnings = []
                            mock_task_service.create_task.return_value = mock_task
                            mock_service.process_translation_sync.return_value = "custom_output.zip"
                            
                            translate_handler(args)
                            
                            mock_service.process_translation_sync.assert_called_once()
                            args, kwargs = mock_service.process_translation_sync.call_args
                            self.assertEqual(kwargs.get('output_filename'), "custom_output.zip")


class TestOutputFilenameEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        """测试前准备"""
        self.service = TranslationService()
        self.task = Mock()
        self.task.task_id = "test_task_id"
        self.task.update_phase_progress = Mock(return_value=True)

    @patch('services.translation_service.PdfGenerator')
    def test_pdf_output_with_empty_output_filename(self, MockPdfGenerator):
        """测试 PDF 输出使用空字符串作为 output_filename"""
        mock_generator = Mock()
        MockPdfGenerator.return_value = mock_generator
        
        result = self.service.generate_pdf_output(
            task=self.task,
            input_filepath="/input/test.pdf",
            unique_id="abc123",
            filename="test.pdf",
            translated_content={},
            target_lang="zh",
            output_path="/output",
            output_filename=""
        )
        
        self.assertEqual(result, "translated_abc123_test.pdf")

    @patch('services.translation_service.DocxGenerator')
    def test_docx_output_with_empty_output_filename(self, MockDocxGenerator):
        """测试 DOCX 输出使用空字符串作为 output_filename"""
        mock_generator = Mock()
        MockDocxGenerator.return_value = mock_generator
        
        result = self.service.generate_docx_output(
            task=self.task,
            unique_id="abc123",
            filename="test.pdf",
            translated_content={},
            extracted_images=[],
            target_lang="zh",
            output_path="/output",
            output_filename=""
        )
        
        self.assertEqual(result, "translated_abc123_test.docx")

    @patch('services.translation_service.create_zip')
    def test_single_zip_with_empty_output_filename(self, mock_create_zip):
        """测试单个 Markdown 压缩使用空字符串作为 output_filename"""
        result = self.service._generate_single_zip(
            task=self.task,
            unique_id="abc123",
            filename="test.pdf",
            md_filepath="/tmp/translated_test.md",
            output_path="/output",
            output_filename="",
            tmp_dir="/tmp"
        )
        
        self.assertEqual(result, "translated_abc123_test.zip")


if __name__ == '__main__':
    unittest.main()
