# -*- coding: utf-8 -*-
"""
PDF指定页翻译集成测试
"""

import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from services.translation_service import translation_service

class TestPdfPageTranslationIntegration:
    """PDF指定页翻译集成测试类"""
    
    def test_process_translation_with_page_range(self):
        """测试翻译服务处理指定页码范围"""
        # 创建模拟任务对象
        mock_task = MagicMock()
        mock_task.is_canceled.return_value = False
        mock_task.update_progress.return_value = True
        mock_task.set_status.return_value = None
        mock_task.set_result.return_value = None
        mock_task.task_id = "test_task_id"
        mock_task.filename = "test_file.pdf"
        
        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_pdf_path = f.name
        
        try:
            # 使用PyMuPDF创建一个简单的PDF文件，包含3页
            import fitz
            doc = fitz.open()
            for i in range(3):
                page = doc.new_page()
                page.insert_text((50, 50), f"Page {i+1} content")
            doc.save(temp_pdf_path)
            doc.close()
            
            # 模拟PDF提取结果
            from models.extraction import PdfExtraction, PdfPage, PdfTable
            from models.text_block import TextBlock
            
            # 创建3个页面的测试数据
            pages = []
            for i in range(3):
                page_num = i + 1
                text_blocks = [
                    TextBlock(
                        block_no=i*10+1,
                        text=f"Page {page_num} text block 1",
                        bbox=(50, 50, 200, 70),
                        block_type=0
                    ),
                    TextBlock(
                        block_no=i*10+2,
                        text=f"Page {page_num} text block 2",
                        bbox=(50, 80, 200, 100),
                        block_type=0
                    )
                ]
                page = PdfPage(page_num=page_num, text_blocks=text_blocks)
                pages.append(page)
            
            extracted_content = PdfExtraction(total_pages=3, pages=pages, tables=[])
            
            # 模拟PDF提取器
            with patch('services.translation_service.pdf_extractor') as mock_pdf_extractor:
                mock_pdf_extractor.extract_text.return_value = extracted_content
                
                # 模拟翻译器
                with patch('services.translation_service.translation_service.get_translator') as mock_get_translator:
                    mock_translator = MagicMock()
                    mock_translator.translate.return_value = "Translated text"
                    mock_get_translator.return_value = mock_translator
                    
                    # 模拟文本处理函数
                    with patch('services.translation_service.merge_semantic_blocks') as mock_merge:
                        # 模拟合并后的块
                        merged_blocks = [
                            {
                                'block_text': "Page 1 text block 1 Page 1 text block 2",
                                'original_blocks': [
                                    {'text_block': pages[0].text_blocks[0], 'page_num': 1, 'index': 0},
                                    {'text_block': pages[0].text_blocks[1], 'page_num': 1, 'index': 1}
                                ]
                            },
                            {
                                'block_text': "Page 2 text block 1 Page 2 text block 2",
                                'original_blocks': [
                                    {'text_block': pages[1].text_blocks[0], 'page_num': 2, 'index': 2},
                                    {'text_block': pages[1].text_blocks[1], 'page_num': 2, 'index': 3}
                                ]
                            },
                            {
                                'block_text': "Page 3 text block 1 Page 3 text block 2",
                                'original_blocks': [
                                    {'text_block': pages[2].text_blocks[0], 'page_num': 3, 'index': 4},
                                    {'text_block': pages[2].text_blocks[1], 'page_num': 3, 'index': 5}
                                ]
                            }
                        ]
                        mock_merge.return_value = (merged_blocks, {})
                        
                        # 模拟文本拆分函数
                        with patch('services.translation_service.split_translated_result') as mock_split:
                            mock_split.return_value = ["Translated block 1", "Translated block 2"]
                            
                            # 模拟PDF生成器
                            with patch('services.translation_service.PdfGenerator') as mock_pdf_generator:
                                mock_pdf_gen_instance = MagicMock()
                                mock_pdf_generator.return_value = mock_pdf_gen_instance
                                
                                # 模拟remove_file函数，阻止临时文件被删除
                                with patch('services.translation_service.remove_file') as mock_remove_file:
                                    
                                    # 测试1：翻译所有页面（空页码范围）
                                    translation_service.process_translation(
                                        mock_task, temp_pdf_path, "en", "zh", "silicon_flow", 
                                        "test_unique_id", "test_file.pdf", "技术文档", "", ""
                                    )
                                    
                                    # 验证PDF生成器被调用
                                    mock_pdf_gen_instance.generate_pdf.assert_called()
                                    
                                    # 重置模拟调用计数
                                    mock_pdf_gen_instance.generate_pdf.reset_mock()
                                    
                                    # 测试2：翻译单个页面（页码1）
                                    translation_service.process_translation(
                                        mock_task, temp_pdf_path, "en", "zh", "silicon_flow", 
                                        "test_unique_id", "test_file.pdf", "技术文档", "", "1"
                                    )
                                    
                                    # 验证PDF生成器被调用
                                    mock_pdf_gen_instance.generate_pdf.assert_called()
                                    
                                    # 重置模拟调用计数
                                    mock_pdf_gen_instance.generate_pdf.reset_mock()
                                    
                                    # 测试3：翻译页码范围1-2
                                    translation_service.process_translation(
                                        mock_task, temp_pdf_path, "en", "zh", "silicon_flow", 
                                        "test_unique_id", "test_file.pdf", "技术文档", "", "1-2"
                                    )
                                    
                                    # 验证PDF生成器被调用
                                    mock_pdf_gen_instance.generate_pdf.assert_called()
                                
        finally:
            # 清理临时文件
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
    
    def test_process_translation_with_no_matching_pages(self):
        """测试翻译服务处理无匹配页码的情况"""
        # 创建模拟任务对象
        mock_task = MagicMock()
        mock_task.is_canceled.return_value = False
        mock_task.update_progress.return_value = True
        mock_task.set_status.return_value = None
        mock_task.task_id = "test_task_id"
        mock_task.filename = "test_file.pdf"
        
        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_pdf_path = f.name
        
        try:
            # 使用PyMuPDF创建一个简单的PDF文件，包含2页
            import fitz
            doc = fitz.open()
            for i in range(2):
                page = doc.new_page()
                page.insert_text((50, 50), f"Page {i+1} content")
            doc.save(temp_pdf_path)
            doc.close()
            
            # 模拟PDF提取结果
            from models.extraction import PdfExtraction, PdfPage
            from models.text_block import TextBlock
            
            # 创建2个页面的测试数据
            pages = []
            for i in range(2):
                page_num = i + 1
                text_blocks = [
                    TextBlock(
                        block_no=i*10+1,
                        text=f"Page {page_num} text block 1",
                        bbox=(50, 50, 200, 70),
                        block_type=0
                    )
                ]
                page = PdfPage(page_num=page_num, text_blocks=text_blocks)
                pages.append(page)
            
            extracted_content = PdfExtraction(total_pages=2, pages=pages, tables=[])
            
            # 模拟PDF提取器
            with patch('services.translation_service.pdf_extractor') as mock_pdf_extractor:
                mock_pdf_extractor.extract_text.return_value = extracted_content
                
                # 测试：翻译不存在的页码
                translation_service.process_translation(
                    mock_task, temp_pdf_path, "en", "zh", "silicon_flow", 
                    "test_unique_id", "test_file.pdf", "技术文档", "", "3"
                )
                
                # 验证任务进度被更新为100%
                mock_task.update_progress.assert_any_call(100, '没有找到需要翻译的文本块')
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)