import logging
import fitz

logger = logging.getLogger(__name__)

def analyze_text_block_style(block, text_dict):
    """分析文本块的样式
    
    Args:
        block: blocks级别文本块
        text_dict: dict级别文本信息
        
    Returns:
        dict: 文本块样式信息
    """
    # 查找最匹配的dict级别块
    matched_block = find_matching_block(block, text_dict)
    if not matched_block:
        return {}
    
    # 分析span样式
    span_styles = analyze_span_styles(matched_block)
    if not span_styles:
        return {}
    
    # 计算主要样式
    main_style = calculate_main_style(span_styles)
    return main_style

def find_matching_block(block, text_dict):
    """查找与blocks级别块匹配的dict级别块
    
    Args:
        block: blocks级别文本块 (x0, y0, x1, y1, text, block_no, block_type)
        text_dict: dict级别文本信息
        
    Returns:
        dict: 匹配的dict级别块
    """
    try:
        x0, y0, x1, y1, _, block_no, _ = block
        
        # 计算当前块的中心点
        current_center_x = (x0 + x1) / 2
        current_center_y = (y0 + y1) / 2
        current_point = fitz.Point(current_center_x, current_center_y)
        current_rect = fitz.Rect(x0, y0, x1, y1)
        
        # 查找最匹配的dict级别块
        matched_block = None
        max_overlap = 0
        
        for dict_block in text_dict.get("blocks", []):
            if dict_block["type"] != 0:  # 只处理文本块
                continue
            
            dict_x0, dict_y0, dict_x1, dict_y1 = dict_block["bbox"]
            dict_rect = fitz.Rect(dict_x0, dict_y0, dict_x1, dict_y1)
            
            # 检查中心点是否在dict块内
            if dict_rect.contains(current_point):
                # 计算重叠面积
                intersection = dict_rect.intersect(current_rect)
                overlap_area = intersection.width * intersection.height
                
                if overlap_area > max_overlap:
                    max_overlap = overlap_area
                    matched_block = dict_block
        
        # 如果没有找到包含中心点的块，尝试使用重叠面积最大的块
        if matched_block is None:
            for dict_block in text_dict.get("blocks", []):
                if dict_block["type"] != 0:
                    continue
                
                dict_x0, dict_y0, dict_x1, dict_y1 = dict_block["bbox"]
                dict_rect = fitz.Rect(dict_x0, dict_y0, dict_x1, dict_y1)
                
                intersection = dict_rect.intersect(current_rect)
                overlap_area = intersection.width * intersection.height
                
                if overlap_area > max_overlap:
                    max_overlap = overlap_area
                    matched_block = dict_block
        
        return matched_block
    except Exception as e:
        logger.warning(f"查找匹配块失败: {e}")
        return None

def analyze_span_styles(block):
    """分析文本块中span的样式
    
    Args:
        block: dict级别文本块
        
    Returns:
        list: span样式列表
    """
    span_styles = []
    
    try:
        # 遍历块内的行
        for line in block.get("lines", []):
            # 遍历行内的span（包含相同属性的文本）
            for span in line.get("spans", []):
                # 提取详细属性
                font = span.get("font", "")
                size = span.get("size", 10)
                color = span.get("color", 0)
                flags = span.get("flags", 0)
                text = span.get("text", "")
                span_length = len(text)
                
                # 记录span的样式信息和长度
                span_styles.append({
                    "font": font,
                    "font_size": size,
                    "color": color,
                    "flags": flags,
                    "length": span_length
                })
                logger.debug(f"span样式: 字体='{font}', 大小={size}, 颜色={color}, 长度={span_length}")
    except Exception as e:
        logger.warning(f"分析span样式失败: {e}")
    
    return span_styles

def calculate_main_style(span_styles):
    """计算主要样式（长度最长的span的样式）
    
    Args:
        span_styles (list): span样式列表
        
    Returns:
        dict: 主要样式
    """
    if not span_styles:
        return {}
    
    # 按长度排序，选择最长的span的样式
    span_styles.sort(key=lambda x: x["length"], reverse=True)
    main_style = span_styles[0]
    
    logger.debug(f"主要样式: 字体='{main_style['font']}', 大小={main_style['font_size']}, 颜色={main_style['color']}")
    return main_style

def update_text_block_style(text_block, style_info):
    """更新文本块的样式信息
    
    Args:
        text_block: TextBlock对象
        style_info (dict): 样式信息
    """
    if not style_info:
        return
    
    try:
        # 更新字体信息
        if 'font' in style_info:
            text_block.font = style_info['font']
        
        # 更新字体大小
        if 'font_size' in style_info:
            text_block.font_size = style_info['font_size']
        
        # 更新颜色
        if 'color' in style_info:
            text_block.color = style_info['color']
        
        # 更新flags（粗体、斜体等）
        if 'flags' in style_info:
            text_block.flags = style_info['flags']
            # 根据flags计算粗体和斜体
            text_block.bold = (style_info['flags'] & 1) != 0
            text_block.italic = (style_info['flags'] & 2) != 0
    except Exception as e:
        logger.warning(f"更新文本块样式失败: {e}")

def extract_block_styles(blocks, text_dict):
    """提取所有文本块的样式
    
    Args:
        blocks: blocks级别文本块列表
        text_dict: dict级别文本信息
        
    Returns:
        dict: 按block_no组织的样式信息
    """
    block_styles = {}
    
    for block in blocks:
        try:
            _, _, _, _, _, block_no, block_type = block
            if block_type != 0:  # 只处理文本块
                continue
            
            style_info = analyze_text_block_style(block, text_dict)
            if style_info:
                block_styles[block_no] = style_info
                logger.debug(f"块 {block_no} 样式: {style_info}")
        except Exception as e:
            logger.warning(f"提取块样式失败: {e}")
    
    return block_styles

def analyze_page_styles(page):
    """分析页面的文本样式
    
    Args:
        page: PyMuPDF页面对象
        
    Returns:
        dict: 页面样式信息
    """
    try:
        # 提取blocks级别文本
        blocks = page.get_text("blocks", flags=1)
        
        # 提取dict级别文本信息
        text_dict = page.get_text("dict", flags=1)
        
        # 提取所有块的样式
        block_styles = extract_block_styles(blocks, text_dict)
        
        return block_styles
    except Exception as e:
        logger.warning(f"分析页面样式失败: {e}")
        return {}
