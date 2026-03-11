class MergedBlock:
    """合并块模型
    
    封装合并后的语义块的所有属性，包括文本内容、原始块引用和样式信息
    """
    
    def __init__(self, block_text, original_blocks, max_width, max_height):
        """初始化合并块
        
        Args:
            block_text (str): 合并后的文本
            original_blocks (list[TextBlock]): 原始TextBlock对象列表
            max_width (float): 原始块最大宽度
            max_height (float): 原始块最大高度
        """
        self.block_text = block_text
        self.original_blocks = original_blocks
        self.max_width = max_width
        self.max_height = max_height
        
        # 从第一个原始块中提取样式信息和页码
        if original_blocks:
            first_block = original_blocks[0]
            self.font = first_block.font
            self.font_size = first_block.font_size
            self.color = first_block.color
            self.flags = first_block.flags
            self.bold = first_block.bold
            self.italic = first_block.italic
            self.page_num = first_block.page_num
            
        else:
            # 默认值
            self.font = ""
            self.font_size = 0.0
            self.color = 0
            self.flags = 0
            self.bold = False
            self.italic = False
            self.page_num = 0
    
    def to_dict(self):
        """转换为字典格式
        
        Returns:
            dict: 包含所有属性的字典
        """
        return {
            'block_text': self.block_text,
            'original_blocks': self.original_blocks,
            'max_width': self.max_width,
            'max_height': self.max_height,
            'font': self.font,
            'font_size': self.font_size,
            'color': self.color,
            'flags': self.flags,
            'bold': self.bold,
            'italic': self.italic,
            'page_num': self.page_num
        }
