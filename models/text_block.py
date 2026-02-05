class TextBlock:
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
        self.block_text = text.strip()
        self.block_bbox = bbox
        self.block_type = block_type
        self.page_num = page_num  # 添加页面号属性
        self.is_body_text = True  # 添加是否为正文的属性，默认为True
        # 样式信息
        self.font = ""
        self.font_size = 0.0
        self.color = 0
        self.flags = 0
        self.bold = False
        self.italic = False
        self.underline = False
        self.strikethrough = False
    
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
            'is_body_text': self.is_body_text,  # 包含是否为正文的属性
            'font': self.font,
            'font_size': self.font_size,
            'color': self.color,
            'flags': self.flags,
            'bold': self.bold,
            'italic': self.italic,
            'underline': self.underline,
            'strikethrough': self.strikethrough
        }
