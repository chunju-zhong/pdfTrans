# -*- coding: utf-8 -*-
"""
翻译服务测试
"""

import pytest
from services.translation_service import translation_service
from modules.pdf_extractor import pdf_extractor

class TestTranslationService:
    """翻译服务测试类"""
    
    def test_process_translation(self, test_pdf_path):
        """测试翻译服务处理函数
        
        验证翻译服务能够正常处理PdfExtraction对象
        """
        # 先提取PDF文本，验证返回的是PdfExtraction对象
        extracted_content = pdf_extractor.extract_text(test_pdf_path)
        
        # 验证提取结果是PdfExtraction对象
        from models.extraction import PdfExtraction
        assert isinstance(extracted_content, PdfExtraction)
        
        # 验证对象属性访问
        assert hasattr(extracted_content, 'total_pages')
        assert hasattr(extracted_content, 'pages')
        assert hasattr(extracted_content, 'tables')
        
        # 验证pages列表中的元素是PdfPage对象
        from models.extraction import PdfPage
        for page in extracted_content.pages:
            assert isinstance(page, PdfPage)
            assert hasattr(page, 'page_num')
            assert hasattr(page, 'text_blocks')
        
        # 验证tables列表中的元素是PdfTable对象（如果有表格）
        if extracted_content.tables:
            from models.extraction import PdfTable
            for table in extracted_content.tables:
                assert isinstance(table, PdfTable)
                assert hasattr(table, 'page_num')
                assert hasattr(table, 'table_idx')
                assert hasattr(table, 'content')
    
    def test_get_translator(self):
        """测试获取翻译器功能
        
        验证get_translator方法能够正确返回不同类型的翻译器
        """
        # 测试获取百度翻译器
        translator = translation_service.get_translator('baidu')
        assert translator is not None
        
        # 测试获取aiping翻译器
        translator = translation_service.get_translator('aiping')
        assert translator is not None
        
        # 测试获取硅基流动翻译器
        translator = translation_service.get_translator('silicon_flow')
        assert translator is not None
