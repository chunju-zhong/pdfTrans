# -*- coding: utf-8 -*-
"""
PDF提取结果模型
"""

from models.text_block import TextBlock


class PdfPage:
    """单页提取结果模型
    
    表示PDF单页的提取结果，包含页码和文本块列表
    """
    
    def __init__(self, page_num, text_blocks):
        """初始化PdfPage对象
        
        Args:
            page_num (int): 页码
            text_blocks (list[TextBlock]): 文本块列表
        """
        self.page_num = page_num
        self.text_blocks = text_blocks
    
    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含所有属性的字典
        """
        return {
            'page_num': self.page_num,
            'text_blocks': [block.to_dict() for block in self.text_blocks]
        }


class PdfTable:
    """单表提取结果模型
    
    表示PDF单表的提取结果，包含页码、表格索引和表格内容
    """
    
    def __init__(self, page_num, table_idx, content):
        """初始化PdfTable对象
        
        Args:
            page_num (int): 页码
            table_idx (int): 表格索引
            content (list[list[str]]): 表格内容
        """
        self.page_num = page_num
        self.table_idx = table_idx
        self.content = content
    
    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含所有属性的字典
        """
        return {
            'page_num': self.page_num,
            'table_idx': self.table_idx,
            'content': self.content
        }


class PdfExtraction:
    """整体提取结果模型
    
    表示PDF整体的提取结果，包含总页数、每页结果列表和表格列表
    """
    
    def __init__(self, total_pages, pages, tables):
        """初始化PdfExtraction对象
        
        Args:
            total_pages (int): PDF总页数
            pages (list[PdfPage]): 每页结果列表
            tables (list[PdfTable]): 表格列表
        """
        self.total_pages = total_pages
        self.pages = pages
        self.tables = tables
    
    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含所有属性的字典
        """
        return {
            'total_pages': self.total_pages,
            'pages': [page.to_dict() for page in self.pages],
            'tables': [table.to_dict() for table in self.tables]
        }
