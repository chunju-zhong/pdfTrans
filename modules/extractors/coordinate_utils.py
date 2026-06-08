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

def _build_bbox_matrix(rows_data, num_rows, num_cols):
    """将 extract_table_cells_by_bbox 返回的 rows_data 转为行×列 bbox 矩阵

    rows_data 是一个二维列表，每行包含该行各单元格的 bbox tuple 或 None。
    对于合并单元格，PyMuPDF 在被合并的位置返回 None。
    此函数将 rows_data 标准化为 num_rows × num_cols 的矩阵，短行用 None 填充。

    Args:
        rows_data (list[list[tuple | None]]): 从 table.rows 获取的原始行数据
        num_rows (int): 总行数
        num_cols (int): 总列数

    Returns:
        list[list[tuple | None]]: num_rows × num_cols 的 bbox 矩阵
    """
    bbox_matrix = []
    for row_idx in range(num_rows):
        if row_idx < len(rows_data):
            row = rows_data[row_idx]
            # 填充短行
            padded_row = list(row) + [None] * (num_cols - len(row))
            bbox_matrix.append(padded_row[:num_cols])
        else:
            bbox_matrix.append([None] * num_cols)
    return bbox_matrix


def compute_span_from_none_positions(bbox_matrix, num_rows, num_cols):
    """从 bbox_matrix 中 None 的位置推断合并单元格的 row_span/col_span

    PyMuPDF 在合并单元格的被合并位置返回 None。此函数扫描 None 的分布，
    推断每个有效位置跨越的行列数。

    算法：
    1. 先确定每个单元格的 col_span（向右扫描连续 None）
    2. 标记被 col_span 覆盖的 None 位置
    3. 向下扫描 row_span 时，跳过已被 col_span 覆盖的 None
    4. 基于 row_span 重新验证 col_span

    Args:
        bbox_matrix (list[list[tuple | None]]): 行×列 bbox 矩阵
        num_rows (int): 总行数
        num_cols (int): 总列数

    Returns:
        dict: {(row_idx, col_idx): (row_span, col_span)}
    """
    span_map = {}

    # 第一步：确定每个单元格的 col_span（向右扫描同行连续 None）
    # 同时标记被 col_span 覆盖的 None 位置
    col_span_map = {}  # {(row_idx, col_idx): col_span}
    covered_by_col_span = set()  # 被 col_span 覆盖的 None 位置集合

    for row_idx in range(num_rows):
        for col_idx in range(num_cols):
            if row_idx >= len(bbox_matrix) or col_idx >= len(bbox_matrix[row_idx]):
                continue
            if bbox_matrix[row_idx][col_idx] is None:
                continue

            # 向右扫描连续 None，确定 col_span
            col_span = 1
            c = col_idx + 1
            while c < num_cols and c < len(bbox_matrix[row_idx]) and bbox_matrix[row_idx][c] is None:
                col_span += 1
                covered_by_col_span.add((row_idx, c))
                c += 1

            if col_span > 1:
                col_span_map[(row_idx, col_idx)] = col_span

    # 第二步：确定 row_span（向下扫描，跳过已被 col_span 覆盖的 None）
    for row_idx in range(num_rows):
        for col_idx in range(num_cols):
            if row_idx >= len(bbox_matrix) or col_idx >= len(bbox_matrix[row_idx]):
                continue
            if bbox_matrix[row_idx][col_idx] is None:
                continue

            # 向下扫描，跳过已被 col_span 覆盖的 None
            row_span = 1
            r = row_idx + 1
            while r < num_rows:
                if r >= len(bbox_matrix) or col_idx >= len(bbox_matrix[r]):
                    break
                if bbox_matrix[r][col_idx] is not None:
                    break
                # 如果这个 None 已被同行左侧的 col_span 覆盖，则不算入 row_span
                if (r, col_idx) in covered_by_col_span:
                    break
                row_span += 1
                r += 1

            # 获取 col_span
            col_span = col_span_map.get((row_idx, col_idx), 1)

            # 第三步：基于 row_span 重新验证 col_span
            # 如果 row_span > 1，向右扫描时需要验证整列段均为 None（且不被 col_span 覆盖）
            if row_span > 1:
                new_col_span = 1
                c = col_idx + 1
                while c < num_cols:
                    all_none = True
                    for dr in range(row_span):
                        r = row_idx + dr
                        if r >= len(bbox_matrix) or c >= len(bbox_matrix[r]):
                            all_none = False
                            break
                        if bbox_matrix[r][c] is not None:
                            all_none = False
                            break
                    if not all_none:
                        break
                    new_col_span += 1
                    c += 1
                col_span = new_col_span

                # 重新验证 row_span
                while row_span > 1:
                    all_none = True
                    for dc in range(col_span):
                        c = col_idx + dc
                        r = row_idx + row_span - 1
                        if r >= len(bbox_matrix) or c >= len(bbox_matrix[r]):
                            all_none = False
                            break
                        if bbox_matrix[r][c] is not None:
                            all_none = False
                            break
                    if all_none:
                        break
                    row_span -= 1

            if row_span > 1 or col_span > 1:
                span_map[(row_idx, col_idx)] = (row_span, col_span)

    return span_map


def calculate_row_heights_from_bboxes(bbox_matrix):
    """从真实单元格 bbox 推算行高

    同行单元格共享相同的 y0 和 y1（PyMuPDF 保证），
    取该行所有单元格中最大的 (y1 - y0) 作为行高。

    Args:
        bbox_matrix (list[list[tuple | None]]): 行×列 bbox 矩阵

    Returns:
        list[float]: 每行的行高列表
    """
    row_heights = []
    for row in bbox_matrix:
        max_height = 0
        for cell_bbox in row:
            if cell_bbox is not None:
                h = cell_bbox[3] - cell_bbox[1]
                max_height = max(max_height, h)
        if max_height > 0:
            row_heights.append(max_height)
        else:
            row_heights.append(40)  # 默认行高
    return row_heights

def calculate_col_widths_from_bboxes(bbox_matrix, table_bbox):
    """从真实单元格 bbox 推算列宽，支持合并单元格

    对于非合并单元格，宽度直接作为所在列的贡献值。
    对于合并单元格（跨多列），宽度按跨列数等分分配到所跨的各列。
    每列最终宽度取所有贡献值中的最大值。

    合并单元格检测：如果某单元格的 x 范围覆盖了多个"标准列宽"的区域，
    则认为它跨多列。标准列宽 = 表格总宽度 / 总列数。

    Args:
        bbox_matrix (list[list[tuple | None]]): 行×列 bbox 矩阵
        table_bbox (tuple): 表格边界框 (x0, y0, x1, y1)

    Returns:
        list[float]: 每列的列宽列表
    """
    if not bbox_matrix or not table_bbox:
        return []

    num_cols = len(bbox_matrix[0]) if bbox_matrix else 0
    if num_cols == 0:
        return []

    table_x0 = table_bbox[0]
    table_width = table_bbox[2] - table_bbox[0]
    col_width_avg = table_width / num_cols if num_cols > 0 else 100

    # 收集每列的宽度贡献
    col_contributions = [[] for _ in range(num_cols)]

    for row_idx, row in enumerate(bbox_matrix):
        for col_idx, cell_bbox in enumerate(row):
            if cell_bbox is None:
                continue

            cell_x0, cell_y0, cell_x1, cell_y1 = cell_bbox
            cell_width = cell_x1 - cell_x0

            if cell_width <= 0:
                continue

            # 判断跨列数：单元格覆盖了多少个标准列宽的区域
            # 从单元格左边界到右边界，计算跨越的列数
            span = max(1, round(cell_width / col_width_avg))
            # 确保不超出矩阵范围
            span = min(span, num_cols - col_idx)

            if span <= 1:
                # 非合并单元格，直接贡献
                col_contributions[col_idx].append(cell_width)
            else:
                # 合并单元格，等分分配到各列
                per_col_width = cell_width / span
                for k in range(span):
                    col_contributions[col_idx + k].append(per_col_width)

    # 每列取最大贡献值
    col_widths = []
    for col_idx in range(num_cols):
        if col_contributions[col_idx]:
            col_widths.append(max(col_contributions[col_idx]))
        else:
            col_widths.append(col_width_avg)

    # 按比例缩放列宽，使总和等于表格实际宽度
    total_width = sum(col_widths)
    if total_width > 0 and abs(total_width - table_width) > 0.1:
        scale = table_width / total_width
        col_widths = [w * scale for w in col_widths]

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

def create_pdf_cell(cell_info, row_span=1, col_span=1):
    """创建PdfCell对象

    Args:
        cell_info (dict): 单元格信息字典
        row_span (int): 跨行数，默认1
        col_span (int): 跨列数，默认1

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
            col_idx=col_idx,
            row_span=row_span,
            col_span=col_span
        )
    except Exception as e:
        logger.warning(f"创建PdfCell对象失败: {e}")
        return None
