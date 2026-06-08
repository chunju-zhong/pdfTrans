import logging
import os
import fitz
import camelot
from models.extraction import PdfTable
from .coordinate_utils import (
    convert_pdf_to_pymupdf_coords,
    calculate_cell_bbox,
    calculate_row_heights,
    calculate_col_widths,
    _build_bbox_matrix,
    calculate_row_heights_from_bboxes,
    calculate_col_widths_from_bboxes,
    create_cell_info,
    create_pdf_cell,
    compute_span_from_none_positions
)
from .page_utils import process_page_numbers, create_pages_param

logger = logging.getLogger(__name__)

def extract_tables_by_camelot(pdf_path, pages=None):
    """提取PDF中的表格内容，可以指定页面
    
    Args:
        pdf_path (str): PDF文件路径
        pages (list[int] | None): 指定要提取的页码列表（从1开始），None表示提取所有页面
        
    Returns:
        tuple[list[PdfTable], dict]: 包含提取的表格列表和按页码组织的表格边界框字典
            - list[PdfTable]: 提取的表格列表
            - dict: 按页码组织的表格边界框字典，键为页码，值为边界框列表
    """
    if not pdf_path:
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    
    pdf_tables = []
    page_tables = {}
    page_heights = {}
    
    try:
        logger.info(f"开始提取PDF表格: {pdf_path}")
        
        # 检查文件是否存在
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 使用PyMuPDF获取页面高度信息，用于坐标系转换
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            logger.info(f"PDF总页数: {total_pages}")
            
            # 处理页码参数
            one_based_pages, _ = process_page_numbers(pages, total_pages)
            
            # 只获取需要的页面高度
            for page_num in one_based_pages:
                page = doc[page_num - 1]  # 转换为0-based索引
                page_heights[page_num] = page.rect.height
        
        logger.info(f"获取页面高度信息: {page_heights}")
        
        # 构建页码参数
        read_pdf_kwargs = {}
        if pages is not None:
            if one_based_pages:
                pages_param = create_pages_param(one_based_pages)
                read_pdf_kwargs['pages'] = pages_param
            else:
                logger.warning("没有有效的页码，将提取所有页面")
        
        # 使用camelot提取表格
        # 尝试使用lattice模式（基于线条），如果失败则使用stream模式（基于空白）
        try:
            tables = camelot.read_pdf(pdf_path, flavor='lattice', **read_pdf_kwargs)
            logger.info(f"使用lattice模式提取表格: 成功提取{len(tables)}个表格")
        except Exception as e:
            logger.warning(f"lattice模式提取失败: {e}，尝试使用stream模式")
            tables = camelot.read_pdf(pdf_path, flavor='stream', **read_pdf_kwargs)
            logger.info(f"使用stream模式提取表格: 成功提取{len(tables)}个表格")
        
        # 处理提取的表格
        for table_idx, table in enumerate(tables):
            page_num = table.page
            
            # 获取页面高度，用于坐标系转换
            page_height = page_heights.get(page_num, 0)
            logger.info(f"页面{page_num}高度: {page_height}")
            
            # 获取表格边界框
            try:
                if hasattr(table, 'parsing_report') and 'bbox' in table.parsing_report:
                    bbox = table.parsing_report['bbox']
                elif hasattr(table, '_bbox'):
                    bbox = table._bbox
                else:
                    bbox = None
                logger.info(f"表格{table_idx}原始边界框: {bbox}")
                
                # 转换边界框坐标系（从PDF标准坐标系转换为PyMuPDF坐标系）
                if bbox and page_height > 0:
                    bbox = convert_pdf_to_pymupdf_coords(bbox, page_height)
                    logger.info(f"表格{table_idx}转换后边界框: {bbox}")
            except Exception as e:
                logger.warning(f"获取表格边界框失败: {e}")
                bbox = None
            
            # 获取表格内容
            data = table.data
            logger.info(f"表格{table_idx}内容: {data}")
            
            # 构建单元格信息
            cell_info_list = []
            for row_idx, row in enumerate(data):
                for col_idx, text in enumerate(row):
                    # 估算单元格边界框
                    if bbox and page_height > 0:
                        cell_bbox = calculate_cell_bbox(
                            bbox, row_idx, col_idx, len(data), len(row)
                        )
                    else:
                        cell_bbox = (0, 0, 100, 30)  # 默认值
                    
                    cell_info = create_cell_info(text, cell_bbox, row_idx, col_idx)
                    cell_info_list.append(cell_info)
                    logger.debug(f"创建单元格信息: 行={row_idx}, 列={col_idx}, 文本='{text}', 边界框={cell_bbox}")
            
            # 构建单元格二维列表
            # 首先确定表格的行数和列数
            if cell_info_list:
                max_row = max(cell['top'] for cell in cell_info_list)
                max_col = max(cell['left'] for cell in cell_info_list)
                logger.info(f"表格结构: {max_row + 1}行 {max_col + 1}列")
            else:
                max_row = 0
                max_col = 0
                logger.info("表格无内容")
            
            # 创建空的单元格二维列表
            cell_matrix = [[None for _ in range(max_col + 1)] for _ in range(max_row + 1)]
            
            # 填充单元格信息
            for cell_info in cell_info_list:
                row_idx = cell_info['top']
                col_idx = cell_info['left']
                
                # 创建PdfCell对象
                pdf_cell = create_pdf_cell(cell_info)
                if pdf_cell:
                    cell_matrix[row_idx][col_idx] = pdf_cell
                    logger.debug(f"填充单元格: 行={row_idx}, 列={col_idx}, 文本='{cell_info['text']}', 边界框={cell_info['bbox']}")
            
            # 过滤掉空表格
            has_content = any(cell and cell.text.strip() for row in cell_matrix for cell in row)
            if has_content:
                # 计算行高和列宽
                row_heights_list = calculate_row_heights(cell_matrix)
                col_widths_list = calculate_col_widths(cell_matrix, bbox)
                
                logger.info(f"计算的行高: {row_heights_list}")
                logger.info(f"计算的列宽: {col_widths_list}")
                
                # 创建PdfTable对象并添加到pdf_tables列表
                pdf_table = PdfTable(
                    page_num=page_num,
                    table_idx=table_idx,
                    cells=cell_matrix,
                    bbox=bbox,
                    row_heights=row_heights_list,
                    col_widths=col_widths_list
                )
                pdf_tables.append(pdf_table)
                logger.info(f"表格: 第{page_num}页-表格{table_idx}, 包含{len(cell_matrix)}行{len(cell_matrix[0]) if cell_matrix else 0}列, 边界框: {bbox}")
                
                # 按页码组织表格数据
                if page_num not in page_tables:
                    page_tables[page_num] = []
                if bbox:
                    page_tables[page_num].append(bbox)
        
        logger.info(f"表格提取完成: 总表格={len(pdf_tables)}")
        return pdf_tables, page_tables
        
    except FileNotFoundError:
        # 直接重新抛出FileNotFoundError
        raise
    except Exception as e:
        logger.error(f"提取PDF表格时出错: {str(e)}", exc_info=True)
        raise Exception(f"提取PDF表格时出错: {str(e)}")

def extract_table_cells_by_bbox(page, table, table_bbox=None):
    """使用单元格精确bbox提取表格文本，替代table.extract()

    PyMuPDF的table.extract()使用字符中心点归属判断，会将表格标题/脚注
    错误地吸附进单元格。此函数使用单元格精确bbox和50%面积重叠判断，
    从几何位置上确保只有真正属于单元格的文本被提取。

    Args:
        page: PyMuPDF页面对象
        table: PyMuPDF Table对象
        table_bbox: 表格边界框，用于过滤超出表格范围的字符。
                    如果为None，则使用table.bbox。

    Returns:
        tuple: (data, cell_bboxes, rows_data)
            - data: 二维列表，格式与table.extract()一致
            - cell_bboxes: 单元格bbox列表 [(x0,y0,x1,y1), ...]
            - rows_data: 行×列 bbox 矩阵，每行包含该行各单元格的 bbox tuple 或 None
    """
    # 1. 从table.rows获取每行的单元格bbox，构建行×列矩阵
    rows_data = []
    cell_bboxes = []

    for row in table.rows:
        row_cells = []
        for cell in row.cells:
            if cell is not None:
                row_cells.append(tuple(cell))
                cell_bboxes.append(tuple(cell))
            else:
                row_cells.append(None)
        rows_data.append(row_cells)

    if not rows_data:
        return [], [], []

    num_rows = len(rows_data)
    num_cols = max(len(row) for row in rows_data)

    # 2. 获取页面所有字符及其bbox
    rawdict = page.get_text("rawdict", flags=fitz.TEXTFLAGS_TEXT)

    # 收集所有字符
    all_chars = []
    for block in rawdict.get("blocks", []):
        if block["type"] != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    char_bbox = fitz.Rect(char["bbox"])
                    char_area = char_bbox.width * char_bbox.height
                    if char_area > 0:
                        all_chars.append({
                            "char": char["c"],
                            "bbox": char_bbox,
                            "area": char_area,
                            "x0": char_bbox.x0,
                            "y0": char_bbox.y0,
                        })

    # 2.5 过滤超出表格bbox范围的字符
    if table_bbox is None:
        table_bbox = table.bbox
    if table_bbox:
        table_rect = fitz.Rect(table_bbox)
        # 允许少量容差（2像素），避免边界字符被误排除
        table_rect_expanded = fitz.Rect(
            table_rect.x0 - 2,
            table_rect.y0 - 2,
            table_rect.x1 + 2,
            table_rect.y1 + 2
        )
        original_count = len(all_chars)
        filtered_chars = []
        for char_info in all_chars:
            char_center_x = (char_info["x0"] + char_info["bbox"].x1) / 2
            char_center_y = (char_info["y0"] + char_info["bbox"].y1) / 2
            if table_rect_expanded.contains(fitz.Point(char_center_x, char_center_y)):
                filtered_chars.append(char_info)
        if original_count != len(filtered_chars):
            logger.debug(f"表格bbox过滤字符: 原始{original_count}个, 保留{len(filtered_chars)}个, 过滤掉{original_count - len(filtered_chars)}个表外字符")
        all_chars = filtered_chars

    # 3. 为每个单元格分配字符
    # 初始化单元格字符列表
    cell_chars = {}
    for row_idx, row in enumerate(rows_data):
        for col_idx, cell_bbox in enumerate(row):
            if cell_bbox is not None:
                cell_chars[(row_idx, col_idx)] = []

    # 对每个字符，检查与各单元格的重叠
    for char_info in all_chars:
        char_rect = char_info["bbox"]
        char_area = char_info["area"]
        best_overlap_ratio = 0
        best_cell = None

        for row_idx, row in enumerate(rows_data):
            for col_idx, cell_bbox in enumerate(row):
                if cell_bbox is None:
                    continue
                cell_rect = fitz.Rect(cell_bbox)
                try:
                    intersection = char_rect & cell_rect
                    if intersection.is_empty:
                        continue
                    overlap_area = intersection.width * intersection.height
                    overlap_ratio = overlap_area / char_area
                    if overlap_ratio > best_overlap_ratio:
                        best_overlap_ratio = overlap_ratio
                        best_cell = (row_idx, col_idx)
                except Exception:
                    continue

        # 重叠超过50%才分配
        if best_overlap_ratio > 0.5 and best_cell is not None:
            cell_chars[best_cell].append(char_info)

    # 4. 将每个单元格的字符按阅读顺序排序并拼接为文本
    data = []
    for row_idx in range(num_rows):
        row_data = []
        for col_idx in range(num_cols):
            key = (row_idx, col_idx)
            if key in cell_chars and cell_chars[key]:
                # 按y坐标再按x坐标排序
                sorted_chars = sorted(cell_chars[key], key=lambda c: (c["y0"], c["x0"]))
                text = "".join(c["char"] for c in sorted_chars)
                row_data.append(text)
            else:
                row_data.append(None)
        data.append(row_data)

    return data, cell_bboxes, rows_data


def extract_tables_by_pymupdf(pdf_path, pages=None):
    """提取PDF中的表格内容，可以指定页面

    Args:
        pdf_path (str): PDF文件路径
        pages (list[int] | None): 指定要提取的页码列表（从1开始），None表示提取所有页面

    Returns:
        tuple[list[PdfTable], dict, dict]: 包含提取的表格列表、按页码组织的表格边界框字典和按页码组织的单元格边界框字典
            - list[PdfTable]: 提取的表格列表
            - dict: 按页码组织的表格边界框字典，键为页码，值为边界框列表
            - dict: 按页码组织的单元格边界框字典，键为页码，值为单元格bbox列表的列表
    """
    if not pdf_path:
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    
    pdf_tables = []
    page_tables = {}
    page_table_cells = {}

    try:
        logger.info(f"开始使用PyMuPDF提取PDF表格: {pdf_path}")
        
        # 检查文件是否存在
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 使用PyMuPDF打开PDF文件
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            logger.info(f"PDF总页数: {total_pages}")
            
            # 处理页码参数
            one_based_pages, _ = process_page_numbers(pages, total_pages)
            
            # 遍历指定的页面
            for page_num in one_based_pages:
                page_idx = page_num - 1  # 转换为0-based索引
                page = doc[page_idx]
                page_height = page.rect.height
                
                logger.info(f"处理页面: {page_num}")
                
                # 使用PyMuPDF的find_tables()方法提取表格
                try:
                    tables = page.find_tables()
                    logger.info(f"页面{page_num}成功提取{len(tables.tables)}个表格")
                    
                    # 处理提取的表格
                    for table_idx, table in enumerate(tables.tables):
                        # 获取表格边界框
                        bbox = table.bbox
                        logger.info(f"表格{table_idx}边界框: {bbox}")
                        
                        bbox_tuple = bbox
                        
                        # 获取表格内容（使用单元格精确bbox提取，避免标题/脚注被错误包含）
                        rows_data = []
                        try:
                            data, table_cell_bboxes, rows_data = extract_table_cells_by_bbox(page, table, table_bbox=bbox)
                            logger.info(f"表格{table_idx}内容(精确bbox提取): {data}")
                        except Exception as e:
                            logger.warning(f"精确bbox提取失败，回退到table.extract(): {e}")
                            data = table.extract()
                            table_cell_bboxes = []
                            rows_data = []
                            logger.info(f"表格{table_idx}内容(回退): {data}")
                        
                        # 构建单元格信息
                        cell_info_list = []
                        use_real_bbox = bool(rows_data and table_cell_bboxes)

                        if use_real_bbox:
                            # 使用 PyMuPDF 真实单元格 bbox
                            num_rows = len(data)
                            num_cols = max(len(row) for row in data) if data else 0
                            bbox_matrix = _build_bbox_matrix(rows_data, num_rows, num_cols)
                            logger.info(f"表格{table_idx}使用真实单元格bbox，矩阵大小: {num_rows}×{num_cols}")

                        # 基于 bbox_matrix 中 None 的位置推断合并单元格的 span
                        span_map = {}
                        if use_real_bbox:
                            num_rows_span = len(data)
                            num_cols_span = max(len(row) for row in data) if data else 0
                            # 记录 bbox_matrix 的 None 分布
                            for r_idx, r_data in enumerate(bbox_matrix):
                                none_cols = [c for c, v in enumerate(r_data) if v is None]
                                if none_cols:
                                    logger.debug(f"表格{table_idx} bbox_matrix 行{r_idx}: None位置={none_cols}")
                            span_map = compute_span_from_none_positions(bbox_matrix, num_rows_span, num_cols_span)
                            if span_map:
                                logger.debug(f"表格{table_idx}检测到合并单元格: {span_map}")

                        for row_idx, row in enumerate(data):
                            for col_idx, text in enumerate(row):
                                if use_real_bbox and row_idx < len(bbox_matrix) and col_idx < len(bbox_matrix[row_idx]):
                                    cell_bbox = bbox_matrix[row_idx][col_idx]
                                    if cell_bbox is None:
                                        # 合并单元格的被合并位置，跳过不创建 cell_info
                                        logger.debug(f"合并覆盖位置: 行={row_idx}, 列={col_idx}, 设为None")
                                        continue
                                else:
                                    # 回退：均匀分割
                                    if bbox:
                                        cell_bbox = calculate_cell_bbox(
                                            bbox_tuple, row_idx, col_idx, len(data), len(row)
                                        )
                                    else:
                                        cell_bbox = (0, 0, 100, 30)  # 默认值

                                cell_info = create_cell_info(text, cell_bbox, row_idx, col_idx)
                                cell_info_list.append(cell_info)
                                logger.debug(f"创建单元格信息: 行={row_idx}, 列={col_idx}, 文本='{text}', 边界框={cell_bbox}")

                        # 构建单元格二维列表
                        # 首先确定表格的行数和列数
                        if cell_info_list:
                            max_row = max(cell['top'] for cell in cell_info_list)
                            max_col = max(cell['left'] for cell in cell_info_list)
                            logger.info(f"表格结构: {max_row + 1}行 {max_col + 1}列")
                        else:
                            max_row = 0
                            max_col = 0
                            logger.info("表格无内容")

                        # 创建空的单元格二维列表
                        cell_matrix = [[None for _ in range(max_col + 1)] for _ in range(max_row + 1)]

                        # 填充单元格信息
                        for cell_info in cell_info_list:
                            row_idx = cell_info['top']
                            col_idx = cell_info['left']

                            # 从 span_map 获取合并单元格的 row_span / col_span
                            row_span, col_span = span_map.get((row_idx, col_idx), (1, 1))

                            # 创建PdfCell对象
                            pdf_cell = create_pdf_cell(cell_info, row_span=row_span, col_span=col_span)
                            if pdf_cell:
                                cell_matrix[row_idx][col_idx] = pdf_cell
                                logger.debug(f"填充单元格: 行={row_idx}, 列={col_idx}, row_span={row_span}, col_span={col_span}, 文本='{cell_info['text']}', 边界框={cell_info['bbox']}")
                                # 将合并覆盖的位置设为 None
                                if row_span > 1 or col_span > 1:
                                    for dr in range(row_span):
                                        for dc in range(col_span):
                                            if dr == 0 and dc == 0:
                                                continue  # 起始位置已设置
                                            overlap_row = row_idx + dr
                                            overlap_col = col_idx + dc
                                            if overlap_row < len(cell_matrix) and overlap_col < len(cell_matrix[overlap_row]):
                                                cell_matrix[overlap_row][overlap_col] = None
                                                logger.debug(f"合并覆盖位置: 行={overlap_row}, 列={overlap_col}, 设为None")
                        
                        # 过滤掉空表格
                        has_content = any(cell and cell.text.strip() for row in cell_matrix for cell in row)
                        if has_content:
                            # 计算行高和列宽
                            if use_real_bbox:
                                row_heights_list = calculate_row_heights_from_bboxes(bbox_matrix)
                                col_widths_list = calculate_col_widths_from_bboxes(bbox_matrix, bbox_tuple)
                                logger.info(f"从真实bbox计算的行高: {row_heights_list}")
                                logger.info(f"从真实bbox计算的列宽: {col_widths_list}")
                            else:
                                row_heights_list = calculate_row_heights(cell_matrix)
                                col_widths_list = calculate_col_widths(cell_matrix, bbox_tuple)
                                logger.info(f"计算的行高: {row_heights_list}")
                                logger.info(f"计算的列宽: {col_widths_list}")
                            
                            # 创建PdfTable对象并添加到pdf_tables列表
                            pdf_table = PdfTable(
                                page_num=page_num,
                                table_idx=table_idx,
                                cells=cell_matrix,
                                bbox=bbox_tuple,
                                row_heights=row_heights_list,
                                col_widths=col_widths_list
                            )
                            pdf_tables.append(pdf_table)
                            logger.info(f"表格: 第{page_num}页-表格{table_idx}, 包含{len(cell_matrix)}行{len(cell_matrix[0]) if cell_matrix else 0}列, 边界框: {bbox_tuple}")
                            
                            # 按页码组织表格数据
                            if page_num not in page_tables:
                                page_tables[page_num] = []
                            if bbox_tuple:
                                page_tables[page_num].append(bbox_tuple)

                            # 按页码组织单元格bbox数据
                            if page_num not in page_table_cells:
                                page_table_cells[page_num] = []
                            page_table_cells[page_num].append(table_cell_bboxes)
                except Exception as e:
                    logger.warning(f"页面{page_num}提取表格失败: {e}")
                    continue

        logger.info(f"表格提取完成: 总表格={len(pdf_tables)}")
        return pdf_tables, page_tables, page_table_cells

    except FileNotFoundError:
        # 直接重新抛出FileNotFoundError
        raise
    except Exception as e:
        logger.error(f"提取PDF表格时出错: {str(e)}", exc_info=True)
        raise Exception(f"提取PDF表格时出错: {str(e)}")

def get_table_bboxes_by_page(page_tables):
    """按页码组织表格边界框
    
    Args:
        page_tables (dict): 按页码组织的表格边界框字典
        
    Returns:
        dict: 按页码组织的表格边界框字典
    """
    return page_tables

def process_table_data(table):
    """处理表格数据
    
    Args:
        table: 从camelot提取的表格对象
        
    Returns:
        tuple:
            list: 表格数据
            dict: 表格元数据
    """
    try:
        data = table.data
        metadata = {
            'page': table.page,
            'shape': (len(data), len(data[0]) if data else 0)
        }
        
        # 尝试获取表格边界框
        if hasattr(table, 'parsing_report') and 'bbox' in table.parsing_report:
            metadata['bbox'] = table.parsing_report['bbox']
        elif hasattr(table, '_bbox'):
            metadata['bbox'] = table._bbox
        
        return data, metadata
    except Exception as e:
        logger.warning(f"处理表格数据失败: {e}")
        return [], {}
