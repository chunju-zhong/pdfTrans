import logging
from models.extraction import PdfCell

logger = logging.getLogger(__name__)

def convert_pdf_to_pymupdf_coords(bbox, page_height):
    """将PDF标准坐标系转换为PyMuPDF坐标系
    
    Args:
        bbox (tuple): PDF标准坐标系下的边界框 (x0, y0, x1, y1)
        page_height (float): 页面高度
        
    Returns:
        tuple: PyMuPDF坐标系下的边界框 (x0, y0, x1, y1)
    """
    if not bbox or page_height <= 0:
        return bbox
    
    try:
        x0, y0, x1, y1 = bbox
        # PDF标准坐标系：原点在左下角
        # PyMuPDF坐标系：原点在左上角
        new_y0 = page_height - y1
        new_y1 = page_height - y0
        return (x0, new_y0, x1, new_y1)
    except Exception as e:
        logger.warning(f"坐标转换失败: {e}")
        return bbox

def calculate_cell_bbox(table_bbox, row_idx, col_idx, num_rows, num_cols):
    """计算单元格边界框
    
    Args:
        table_bbox (tuple): 表格边界框
        row_idx (int): 行索引
        col_idx (int): 列索引
        num_rows (int): 总行数
        num_cols (int): 总列数
        
    Returns:
        tuple: 单元格边界框
    """
    if not table_bbox:
        return (0, 0, 100, 30)  # 默认值
    
    try:
        table_x0, table_y0, table_x1, table_y1 = table_bbox
        
        # 计算单元格大小
        cell_height = (table_y1 - table_y0) / num_rows
        cell_width = (table_x1 - table_x0) / num_cols
        
        # 计算单元格位置
        x0 = table_x0 + col_idx * cell_width
        y0 = table_y0 + row_idx * cell_height
        x1 = x0 + cell_width
        y1 = y0 + cell_height
        
        return (x0, y0, x1, y1)
    except Exception as e:
        logger.warning(f"计算单元格边界框失败: {e}")
        return (0, 0, 100, 30)  # 默认值

def calculate_row_heights(cell_matrix):
    """计算表格行高
    
    Args:
        cell_matrix (list): 单元格二维列表
        
    Returns:
        list: 行高列表
    """
    row_heights = []
    for row_idx in range(len(cell_matrix)):
        max_height = 0
        for cell in cell_matrix[row_idx]:
            if cell:
                max_height = max(max_height, cell.height)
        if max_height > 0:
            row_heights.append(max_height)
        else:
            row_heights.append(40)  # 默认行高
    return row_heights

def calculate_col_widths(cell_matrix, table_bbox):
    """计算表格列宽
    
    Args:
        cell_matrix (list): 单元格二维列表
        table_bbox (tuple): 表格边界框
        
    Returns:
        list: 列宽列表
    """
    col_widths = []
    if not cell_matrix:
        return col_widths
    
    num_cols = len(cell_matrix[0])
    for col_idx in range(num_cols):
        max_width = 0
        for row in cell_matrix:
            if col_idx < len(row) and row[col_idx]:
                max_width = max(max_width, row[col_idx].width)
        if max_width > 0:
            col_widths.append(max_width)
        else:
            if table_bbox:
                table_width = table_bbox[2] - table_bbox[0]
                col_widths.append(table_width / num_cols)
            else:
                col_widths.append(100)  # 默认列宽
    return col_widths

def create_cell_info(text, bbox, row_idx, col_idx):
    """创建单元格信息字典
    
    Args:
        text (str): 单元格文本
        bbox (tuple): 单元格边界框
        row_idx (int): 行索引
        col_idx (int): 列索引
        
    Returns:
        dict: 单元格信息字典
    """
    return {
        'text': text or '',
        'bbox': bbox,
        'top': row_idx,
        'left': col_idx,
        'x0': bbox[0],
        'y0': bbox[1],
        'x1': bbox[2],
        'y1': bbox[3],
        'width': bbox[2] - bbox[0],
        'height': bbox[3] - bbox[1]
    }

def create_pdf_cell(cell_info):
    """创建PdfCell对象
    
    Args:
        cell_info (dict): 单元格信息字典
        
    Returns:
        PdfCell: PdfCell对象
    """
    try:
        text = cell_info['text'] if cell_info['text'] else ''
        bbox = cell_info['bbox'] if 'bbox' in cell_info else \
               (cell_info['x0'], cell_info['y0'], cell_info['x1'], cell_info['y1'])
        row_idx = cell_info['top']
        col_idx = cell_info['left']
        
        return PdfCell(
            text=text,
            bbox=bbox,
            row_idx=row_idx,
            col_idx=col_idx
        )
    except Exception as e:
        logger.warning(f"创建PdfCell对象失败: {e}")
        return None
