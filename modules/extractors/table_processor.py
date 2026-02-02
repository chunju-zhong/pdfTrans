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
    create_cell_info,
    create_pdf_cell
)
from .page_utils import process_page_numbers, create_pages_param

logger = logging.getLogger(__name__)

def extract_tables(pdf_path, pages=None):
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
