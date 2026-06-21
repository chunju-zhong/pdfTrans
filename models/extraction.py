# -*- coding: utf-8 -*-
"""
PDF提取结果模型
"""

from models.copyable import CopyableMixin
from models.text_block import TextBlock


class PdfPage(CopyableMixin):
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
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建PdfPage对象

        Args:
            data (dict): 包含属性的字典

        Returns:
            PdfPage: 页面对象
        """
        return cls(
            page_num=data['page_num'],
            text_blocks=[TextBlock.from_dict(b) for b in data['text_blocks']],
        )

    def to_dict(self):
        """转换为字典格式

        Returns:
            dict: 包含所有属性的字典
        """
        return {
            'page_num': self.page_num,
            'text_blocks': [block.to_dict() for block in self.text_blocks]
        }


class PdfCell(CopyableMixin):
    """表格单元格模型
    
    表示PDF表格中的单个单元格，包含文本、边界框和大小信息
    """
    
    def __init__(self, text, bbox, row_idx, col_idx, row_span=1, col_span=1, alignment=0, estimated_lines=0):
        """初始化PdfCell对象

        Args:
            text (str): 单元格文本
            bbox (tuple): 单元格边界框 (x0, y0, x1, y1)
            row_idx (int): 行索引
            col_idx (int): 列索引
            row_span (int): 跨行数，默认1
            col_span (int): 跨列数，默认1
            alignment (int): 对齐方式，0=左对齐, 1=居中, 2=右对齐，默认0
            estimated_lines (int): 估算的文本换行行数，默认0
        """
        self.text = text
        self.bbox = bbox
        self.row_idx = row_idx
        self.col_idx = col_idx
        self.row_span = row_span
        self.col_span = col_span
        self.alignment = alignment
        self.estimated_lines = estimated_lines
        # 计算单元格大小
        self.width = bbox[2] - bbox[0]
        self.height = bbox[3] - bbox[1]
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建PdfCell对象

        Args:
            data (dict): 包含属性的字典

        Returns:
            PdfCell: 单元格对象
        """
        obj = cls(
            text=data['text'],
            bbox=tuple(data['bbox']),
            row_idx=data['row_idx'],
            col_idx=data['col_idx'],
        )
        obj.width = data.get('width', 0)
        obj.height = data.get('height', 0)
        obj.row_span = data.get('row_span', 1)
        obj.col_span = data.get('col_span', 1)
        obj.alignment = data.get('alignment', 0)
        obj.estimated_lines = data.get('estimated_lines', 0)
        return obj

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
            'height': self.height,
            'row_span': self.row_span,
            'col_span': self.col_span,
            'alignment': self.alignment,
            'estimated_lines': self.estimated_lines
        }


class PdfTable(CopyableMixin):
    """单表提取结果模型
    
    表示PDF单表的提取结果，包含页码、表格索引、单元格信息和边界框信息
    """
    
    def __init__(self, page_num, table_idx, cells, bbox=None, row_heights=None, col_widths=None, alignment=1):
        """初始化PdfTable对象

        Args:
            page_num (int): 页码
            table_idx (int): 表格索引
            cells (list[list[PdfCell]]): 单元格信息，二维列表
            bbox (tuple): 表格边界框 (x0, y0, x1, y1)
            row_heights (list[float]): 行高列表
            col_widths (list[float]): 列宽列表
            alignment (int): 表格整体对齐方式，0=左对齐, 1=居中, 2=右对齐，默认1
        """
        self.page_num = page_num
        self.table_idx = table_idx
        self.cells = cells
        self.bbox = bbox
        self.row_heights = row_heights or []
        self.col_widths = col_widths or []
        self.alignment = alignment
        # 章节信息
        self.chapter_id = None  # 章节ID
        self.chapter_title = None  # 章节标题
        self.chapter_level = 0  # 章节层级
        self.chapter_number = None  # 章节编号
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建PdfTable对象

        Args:
            data (dict): 包含属性的字典

        Returns:
            PdfTable: 表格对象
        """
        cells = []
        for row_data in data['cells']:
            row = [PdfCell.from_dict(c) if c is not None else None for c in row_data]
            cells.append(row)
        obj = cls(
            page_num=data['page_num'],
            table_idx=data['table_idx'],
            cells=cells,
            bbox=tuple(data['bbox']) if data.get('bbox') else None,
            row_heights=data.get('row_heights', []),
            col_widths=data.get('col_widths', []),
            alignment=data.get('alignment', 1),
        )
        obj.chapter_id = data.get('chapter_id')
        obj.chapter_title = data.get('chapter_title')
        obj.chapter_level = data.get('chapter_level', 0)
        obj.chapter_number = data.get('chapter_number')
        return obj

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
                row_dict.append(cell.to_dict() if cell is not None else None)
            cells_dict.append(row_dict)

        return {
            'page_num': self.page_num,
            'table_idx': self.table_idx,
            'cells': cells_dict,
            'bbox': self.bbox,
            'row_heights': self.row_heights,
            'col_widths': self.col_widths,
            'alignment': self.alignment,
            'chapter_id': self.chapter_id,
            'chapter_title': self.chapter_title,
            'chapter_level': self.chapter_level,
            'chapter_number': self.chapter_number
        }


class PdfImage(CopyableMixin):
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
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建PdfImage对象

        Args:
            data (dict): 包含属性的字典

        Returns:
            PdfImage: 图像对象
        """
        obj = cls(
            page_num=data['page_num'],
            image_idx=data['image_idx'],
            image_path=data['image_path'],
            bbox=tuple(data['bbox']),
        )
        obj.chapter_id = data.get('chapter_id')
        obj.chapter_title = data.get('chapter_title')
        obj.chapter_level = data.get('chapter_level', 0)
        obj.chapter_number = data.get('chapter_number')
        return obj

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


class PdfExtraction(CopyableMixin):
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
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建PdfExtraction对象

        Args:
            data (dict): 包含属性的字典

        Returns:
            PdfExtraction: 提取结果对象
        """
        return cls(
            total_pages=data['total_pages'],
            pages=[PdfPage.from_dict(p) for p in data['pages']],
            tables=[PdfTable.from_dict(t) for t in data['tables']],
            images=[PdfImage.from_dict(i) for i in data.get('images', [])],
        )

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
