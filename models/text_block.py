from models.copyable import CopyableMixin


class TextBlock(CopyableMixin):
    """文本块模型
    
    封装PDF文本块的所有属性，包括内容和样式信息
    """
    
    def __init__(self, block_no, text, bbox, block_type=0, page_num=0):
        """初始化文本块
        
        Args:
            block_no (int): 块序号
            text (str): 文本内容
            bbox (tuple): 块边界框 (x0, y0, x1, y1)
            block_type (int): 块类型
            page_num (int): 页面号
        """
        self.block_no = block_no
        self.block_text = text  # 保留原文中的换行和空格，不做strip处理
        self.block_bbox = bbox
        self.block_type = block_type
        self.page_num = page_num  # 添加页面号属性
        self.is_body_text = True
        self.is_formula = False
        # 章节信息
        self.chapter_id = None  # 章节ID
        self.chapter_title = None  # 章节标题
        self.chapter_level = 0  # 章节层级
        self.chapter_number = None  # 章节编号（如1, 1.1, 1.1.1等）
        # 样式信息
        self.font = ""
        self.font_size = 0.0
        self.color = 0
        self.flags = 0
        self.bold = False
        self.italic = False
        self.underline = False
        self.strikethrough = False
        # 对齐方式
        self.alignment = 0  # 0=左对齐, 1=居中, 2=右对齐
    
    def update_style(self, font="", font_size=0.0, color=0, flags=0):
        """更新文本块样式信息
        
        Args:
            font (str): 字体名称
            font_size (float): 字体大小
            color (int): 颜色值
            flags (int): 样式标记
        """
        self.font = font
        self.font_size = font_size
        self.color = color
        self.flags = flags
        # 解析样式标记
        self.bold = bool(flags & 1)
        self.italic = bool(flags & 2)
        self.underline = bool(flags & 4)
        self.strikethrough = bool(flags & 8)
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建TextBlock对象

        Args:
            data (dict): 包含属性的字典

        Returns:
            TextBlock: 文本块对象
        """
        obj = cls(
            block_no=data['block_no'],
            text=data['block_text'],
            bbox=tuple(data['block_bbox']),
            block_type=data.get('block_type', 0),
            page_num=data.get('page_num', 0),
        )
        obj.is_body_text = data.get('is_body_text', True)
        obj.is_formula = data.get('is_formula', False)
        obj.chapter_id = data.get('chapter_id')
        obj.chapter_title = data.get('chapter_title')
        obj.chapter_level = data.get('chapter_level', 0)
        obj.chapter_number = data.get('chapter_number')
        obj.font = data.get('font', '')
        obj.font_size = data.get('font_size', 0.0)
        obj.color = data.get('color', 0)
        obj.flags = data.get('flags', 0)
        obj.bold = data.get('bold', False)
        obj.italic = data.get('italic', False)
        obj.underline = data.get('underline', False)
        obj.strikethrough = data.get('strikethrough', False)
        obj.alignment = data.get('alignment', 0)
        return obj

    def to_dict(self):
        """转换为字典格式

        Returns:
            dict: 包含所有属性的字典
        """
        return {
            'block_no': self.block_no,
            'block_text': self.block_text,
            'block_bbox': self.block_bbox,
            'block_type': self.block_type,
            'page_num': self.page_num,  # 包含页面号属性
            'is_body_text': self.is_body_text,
            'is_formula': self.is_formula,
            'chapter_id': self.chapter_id,
            'chapter_title': self.chapter_title,
            'chapter_level': self.chapter_level,
            'chapter_number': self.chapter_number,
            'font': self.font,
            'font_size': self.font_size,
            'color': self.color,
            'flags': self.flags,
            'bold': self.bold,
            'italic': self.italic,
            'underline': self.underline,
            'strikethrough': self.strikethrough,
            'alignment': self.alignment,
        }
