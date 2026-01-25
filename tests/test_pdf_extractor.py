#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF提取模块测试
"""

import pytest
from modules.pdf_extractor import pdf_extractor

class TestPdfExtractor:
    """PDF提取模块测试类"""
    
    def test_extract_text(self, test_pdf_path):
        """测试正常PDF文件的文本提取
        
        验证extract_text方法能够正确提取PDF中的文本内容，包括文本块和表格。
        """
        result = pdf_extractor.extract_text(test_pdf_path)
        
        # 验证结果类型
        from models.extraction import PdfExtraction
        assert isinstance(result, PdfExtraction)
        
        # 验证结果属性
        assert hasattr(result, 'total_pages')
        assert hasattr(result, 'pages')
        assert hasattr(result, 'tables')
        
        # 验证页面数量大于0
        assert result.total_pages > 0
        
        # 验证文本内容列表长度与总页数一致
        assert len(result.pages) == result.total_pages
        
        # 验证每个页面都包含正确的属性
        from models.extraction import PdfPage
        for page_content in result.pages:
            assert isinstance(page_content, PdfPage)
            assert hasattr(page_content, 'page_num')
            assert hasattr(page_content, 'text_blocks')
            assert isinstance(page_content.text_blocks, list)
        
        # 验证至少有一个文本块
        assert any(len(page.text_blocks) > 0 for page in result.pages)
    
    def test_extract_text_invalid_file(self, invalid_pdf_path):
        """测试不存在的PDF文件处理
        
        验证extract_text方法在处理不存在的PDF文件时能够正确抛出异常。
        """
        with pytest.raises(FileNotFoundError):
            pdf_extractor.extract_text(invalid_pdf_path)
    
    def test_extract_page_text(self, test_pdf_path):
        """测试指定页面的文本提取
        
        验证extract_page_text方法能够正确提取指定页面的文本内容。
        """
        # 首先获取总页数
        metadata = pdf_extractor.get_metadata(test_pdf_path)
        total_pages = metadata['total_pages']
        
        # 测试提取第一页
        page_text = pdf_extractor.extract_page_text(test_pdf_path, 1)
        
        # 验证结果类型和属性
        from models.extraction import PdfPage
        assert isinstance(page_text, PdfPage)
        assert hasattr(page_text, 'page_num')
        assert hasattr(page_text, 'text_blocks')
        assert page_text.page_num == 1
        assert isinstance(page_text.text_blocks, list)
        
        # 测试提取最后一页
        page_text = pdf_extractor.extract_page_text(test_pdf_path, total_pages)
        assert page_text.page_num == total_pages
    
    def test_extract_page_text_invalid_page(self, test_pdf_path):
        """测试无效页码处理
        
        验证extract_page_text方法在处理无效页码时能够正确抛出异常。
        """
        # 获取总页数
        total_pages = pdf_extractor.get_metadata(test_pdf_path)['total_pages']
        
        # 测试页码小于1
        with pytest.raises(ValueError):
            pdf_extractor.extract_page_text(test_pdf_path, 0)
        
        # 测试页码大于总页数
        with pytest.raises(ValueError):
            pdf_extractor.extract_page_text(test_pdf_path, total_pages + 1)
    
    def test_extract_page_text_invalid_file(self, invalid_pdf_path):
        """测试不存在的PDF文件处理
        
        验证extract_page_text方法在处理不存在的PDF文件时能够正确抛出异常。
        """
        with pytest.raises(FileNotFoundError):
            pdf_extractor.extract_page_text(invalid_pdf_path, 1)
    
    def test_extract_tables(self, test_pdf_path):
        """测试表格提取功能
        
        验证extract_tables方法能够正确提取PDF中的表格内容。
        """
        tables = pdf_extractor.extract_tables(test_pdf_path)
        
        # 验证返回结果是列表
        assert isinstance(tables, list)
        
        # 验证每个表格项的结构
        from models.extraction import PdfTable
        for table in tables:
            assert isinstance(table, PdfTable)
            assert hasattr(table, 'page_num')
            assert hasattr(table, 'table_idx')
            assert hasattr(table, 'content')
            assert isinstance(table.content, list)
    
    def test_extract_tables_invalid_file(self, invalid_pdf_path):
        """测试不存在的PDF文件处理
        
        验证extract_tables方法在处理不存在的PDF文件时能够正确抛出异常。
        """
        with pytest.raises(FileNotFoundError):
            pdf_extractor.extract_tables(invalid_pdf_path)
    
    def test_get_metadata(self, test_pdf_path):
        """测试元数据提取
        
        验证get_metadata方法能够正确提取PDF的元数据。
        """
        metadata = pdf_extractor.get_metadata(test_pdf_path)
        
        # 验证元数据结构
        assert 'title' in metadata
        assert 'author' in metadata
        assert 'subject' in metadata
        assert 'keywords' in metadata
        assert 'creator' in metadata
        assert 'producer' in metadata
        assert 'creation_date' in metadata
        assert 'modification_date' in metadata
        assert 'total_pages' in metadata
        
        # 验证总页数大于0
        assert metadata['total_pages'] > 0
    
    def test_get_metadata_invalid_file(self, invalid_pdf_path):
        """测试不存在的PDF文件处理
        
        验证get_metadata方法在处理不存在的PDF文件时能够正确抛出异常。
        """
        with pytest.raises(FileNotFoundError):
            pdf_extractor.get_metadata(invalid_pdf_path)