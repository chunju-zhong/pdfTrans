#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF提取模块测试
"""

import pytest
from modules.pdf_extractor import PdfExtractor

class TestPdfExtractor:
    """PDF提取模块测试类"""
    
    def test_extract(self, test_pdf_path):
        """测试正常PDF文件的文本提取
        
        验证extract方法能够正确提取PDF中的文本内容，包括文本块和表格。
        """
        pdf_extractor = PdfExtractor(test_pdf_path)
        result = pdf_extractor.extract()
        
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
    
    def test_extract_invalid_file(self, invalid_pdf_path):
        """测试不存在的PDF文件处理
        
        验证extract方法在处理不存在的PDF文件时能够正确抛出异常。
        """
        with pytest.raises(FileNotFoundError):
            pdf_extractor = PdfExtractor(invalid_pdf_path)
            pdf_extractor.extract()
    

    
    def test_extract_tables(self, test_pdf_path):
        """测试表格提取功能
        
        验证extract_tables方法能够正确提取PDF中的表格内容。
        """
        pdf_extractor = PdfExtractor(test_pdf_path)
        tables, page_tables = pdf_extractor.extract_tables()
        
        # 验证返回结果类型
        assert isinstance(tables, list)
        assert isinstance(page_tables, dict)
        
        # 验证每个表格项的结构
        from models.extraction import PdfTable
        for table in tables:
            assert isinstance(table, PdfTable)
            assert hasattr(table, 'page_num')
            assert hasattr(table, 'table_idx')
            assert hasattr(table, 'cells')
            assert isinstance(table.cells, list)
    
    def test_extract_tables_invalid_file(self, invalid_pdf_path):
        """测试不存在的PDF文件处理
        
        验证extract_tables方法在处理不存在的PDF文件时能够正确抛出异常。
        """
        with pytest.raises(FileNotFoundError):
            pdf_extractor = PdfExtractor(invalid_pdf_path)
            pdf_extractor.extract_tables()
    
    def test_extract_tables_with_pages(self, test_pdf_path):
        """测试指定页面的表格提取
        
        验证extract_tables方法能够正确提取指定页面的表格内容。
        """
        # 创建PDF提取器实例
        pdf_extractor = PdfExtractor(test_pdf_path)
        
        # 首先获取总页数
        metadata = pdf_extractor.get_metadata()
        total_pages = metadata['total_pages']
        
        # 测试提取第一页
        tables, page_tables = pdf_extractor.extract_tables(pages=[1])
        assert isinstance(tables, list)
        assert isinstance(page_tables, dict)
        
        # 验证提取的表格都来自第一页
        from models.extraction import PdfTable
        for table in tables:
            assert isinstance(table, PdfTable)
            assert table.page_num == 1
        
        # 验证page_tables只包含第一页
        assert set(page_tables.keys()) <= {1}
        
        # 测试提取多个页面
        if total_pages >= 2:
            tables, page_tables = pdf_extractor.extract_tables(pages=[1, 2])
            assert isinstance(tables, list)
            assert isinstance(page_tables, dict)
            
            # 验证提取的表格都来自指定页面
            valid_pages = {1, 2}
            for table in tables:
                assert isinstance(table, PdfTable)
                assert table.page_num in valid_pages
            
            # 验证page_tables只包含指定页面
            assert set(page_tables.keys()) <= valid_pages
        
        # 测试提取不存在的页面（应该忽略）
        tables, page_tables = pdf_extractor.extract_tables(pages=[999, 1])
        assert isinstance(tables, list)
        assert isinstance(page_tables, dict)
        
        # 验证提取的表格都来自有效页面
        for table in tables:
            assert isinstance(table, PdfTable)
            assert table.page_num == 1
        
        # 验证page_tables只包含有效页面
        assert set(page_tables.keys()) <= {1}
    
    def test_get_metadata(self, test_pdf_path):
        """测试元数据提取
        
        验证get_metadata方法能够正确提取PDF的元数据。
        """
        pdf_extractor = PdfExtractor(test_pdf_path)
        metadata = pdf_extractor.get_metadata()
        
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
            pdf_extractor = PdfExtractor(invalid_pdf_path)
            pdf_extractor.get_metadata()
    
    def test_total_pages(self, test_pdf_path):
        """测试 total_pages 属性
        
        验证 total_pages 属性能够正确获取PDF文件的总页数。
        """
        # 创建PDF提取器实例
        pdf_extractor = PdfExtractor(test_pdf_path)
        
        # 验证 total_pages 属性存在且大于0
        assert hasattr(pdf_extractor, 'total_pages')
        assert pdf_extractor.total_pages > 0
        
        # 验证 total_pages 属性与 metadata 中的总页数一致
        metadata = pdf_extractor.get_metadata()
        assert pdf_extractor.total_pages == metadata['total_pages']