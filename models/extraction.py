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


class PdfCell:
    """表格单元格模型
    
    表示PDF表格中的单个单元格，包含文本、边界框和大小信息
    """
    
    def __init__(self, text, bbox, row_idx, col_idx):
        """初始化PdfCell对象
        
        Args:
            text (str): 单元格文本
            bbox (tuple): 单元格边界框 (x0, y0, x1, y1)
            row_idx (int): 行索引
            col_idx (int): 列索引
        """
        self.text = text
        self.bbox = bbox
        self.row_idx = row_idx
        self.col_idx = col_idx
        # 计算单元格大小
        self.width = bbox[2] - bbox[0]
        self.height = bbox[3] - bbox[1]
    
    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含所有属性的字典
        """
        return {
            'text': self.text,
            'bbox': self.bbox,
            'row_idx': self.row_idx,
            'col_idx': self.col_idx,
            'width': self.width,
            'height': self.height
        }


class PdfTable:
    """单表提取结果模型
    
    表示PDF单表的提取结果，包含页码、表格索引、单元格信息和边界框信息
    """
    
    def __init__(self, page_num, table_idx, cells, bbox=None, row_heights=None, col_widths=None):
        """初始化PdfTable对象
        
        Args:
            page_num (int): 页码
            table_idx (int): 表格索引
            cells (list[list[PdfCell]]): 单元格信息，二维列表
            bbox (tuple): 表格边界框 (x0, y0, x1, y1)
            row_heights (list[float]): 行高列表
            col_widths (list[float]): 列宽列表
        """
        self.page_num = page_num
        self.table_idx = table_idx
        self.cells = cells
        self.bbox = bbox
        self.row_heights = row_heights or []
        self.col_widths = col_widths or []
        # 章节信息
        self.chapter_id = None  # 章节ID
        self.chapter_title = None  # 章节标题
        self.chapter_level = 0  # 章节层级
        self.chapter_number = None  # 章节编号
    
    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含所有属性的字典
        """
        # 转换cells为字典格式
        cells_dict = []
        for row in self.cells:
            row_dict = []
            for cell in row:
                row_dict.append(cell.to_dict())
            cells_dict.append(row_dict)
        
        return {
            'page_num': self.page_num,
            'table_idx': self.table_idx,
            'cells': cells_dict,
            'bbox': self.bbox,
            'row_heights': self.row_heights,
            'col_widths': self.col_widths,
            'chapter_id': self.chapter_id,
            'chapter_title': self.chapter_title,
            'chapter_level': self.chapter_level,
            'chapter_number': self.chapter_number
        }


class PdfImage:
    """单图提取结果模型
    
    表示PDF单图的提取结果，包含页码、图像索引、图像路径和位置信息
    """
    
    def __init__(self, page_num, image_idx, image_path, bbox):
        """初始化PdfImage对象
        
        Args:
            page_num (int): 页码
            image_idx (int): 图像索引
            image_path (str): 图像保存路径
            bbox (tuple): 图像位置 (x0, y0, x1, y1)
        """
        self.page_num = page_num
        self.image_idx = image_idx
        self.image_path = image_path
        self.bbox = bbox
        # 章节信息
        self.chapter_id = None  # 章节ID
        self.chapter_title = None  # 章节标题
        self.chapter_level = 0  # 章节层级
        self.chapter_number = None  # 章节编号
    
    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含所有属性的字典
        """
        return {
            'page_num': self.page_num,
            'image_idx': self.image_idx,
            'image_path': self.image_path,
            'bbox': self.bbox,
            'chapter_id': self.chapter_id,
            'chapter_title': self.chapter_title,
            'chapter_level': self.chapter_level,
            'chapter_number': self.chapter_number
        }


class PdfExtraction:
    """整体提取结果模型
    
    表示PDF整体的提取结果，包含总页数、每页结果列表、表格列表和图像列表
    """
    
    def __init__(self, total_pages, pages, tables, images=None):
        """初始化PdfExtraction对象
        
        Args:
            total_pages (int): PDF总页数
            pages (list[PdfPage]): 每页结果列表
            tables (list[PdfTable]): 表格列表
            images (list[PdfImage]): 图像列表
        """
        self.total_pages = total_pages
        self.pages = pages
        self.tables = tables
        self.images = images or []
    
    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含所有属性的字典
        """
        return {
            'total_pages': self.total_pages,
            'pages': [page.to_dict() for page in self.pages],
            'tables': [table.to_dict() for table in self.tables],
            'images': [image.to_dict() for image in self.images]
        }
