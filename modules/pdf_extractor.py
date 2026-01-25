import fitz  # PyMuPDF
import pdfplumber
import os
import logging
from models.text_block import TextBlock
from models.extraction import PdfPage, PdfTable, PdfExtraction

logger = logging.getLogger(__name__)


class PdfExtractor:
    """PDF文本提取类
    
    负责从PDF文件中提取文本内容，包括普通文本和表格内容，并保留文本的位置信息。
    """
    
    def __init__(self):
        """初始化PdfExtractor对象"""
        pass
    
    def extract_text(self, pdf_path):
        """提取PDF中的所有文本内容
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            PdfExtraction: 包含提取的文本内容和元数据的对象
                - total_pages (int): PDF总页数
                - pages (list[PdfPage]): 每页的文本内容列表
                    - page_num (int): 页码
                    - text_blocks (list[TextBlock]): 文本块列表，按垂直位置从上到下排序
                - tables (list[PdfTable]): 提取的表格列表
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        result = {
            'total_pages': 0,
            'pages': [],
            'tables': []
        }
        
        try:
            logger.info(f"开始提取PDF: {pdf_path}")
            
            # 使用PyMuPDF提取普通文本
            with fitz.open(pdf_path) as doc:
                result['total_pages'] = len(doc)
                logger.info(f"PDF总页数: {len(doc)}")
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # 1. 提取完整文本块（blocks级别，适合翻译）
                    # 先提取blocks级别，以便后续为dicts添加block_no
                    # 提取blocks级别的文本块信息，flags=1保持原始顺序
                    blocks = page.get_text("blocks", flags=1)
                    
                    # 创建TextBlock对象字典，用于存储每个块的完整信息
                    text_block_objects = {}
                    
                    # 过滤非文本块，仅保留有效文本块并创建TextBlock对象
                    for block in blocks:
                        x0, y0, x1, y1, text, block_no, block_type = block
                        if block_type == 0 and text.strip():
                            # 创建TextBlock对象
                            text_block = TextBlock(
                                block_no=block_no,
                                text=text,
                                bbox=(x0, y0, x1, y1),
                                block_type=block_type
                            )
                            text_block_objects[block_no] = text_block
                    
                    # 2. 使用dict模式提取详细文本信息，包括字体属性，添加flags=1保持原始顺序
                    text_dict = page.get_text("dict", flags=1)
                    
                    # 更新TextBlock对象的样式信息
                    for block in text_dict.get("blocks", []):
                        if block["type"] == 0:  # 文本块
                            block_x0 = block["bbox"][0]
                            block_y0 = block["bbox"][1]
                            block_x1 = block["bbox"][2]
                            block_y1 = block["bbox"][3]
                            
                            # 计算当前块的中心点
                            current_center_x = (block_x0 + block_x1) / 2
                            current_center_y = (block_y0 + block_y1) / 2
                            
                            # 查找最匹配的blocks级别块编号
                            matched_block_no = None
                            min_distance = float('inf')
                            max_overlap = 0
                            
                            for block_no, text_block in text_block_objects.items():
                                block_info_rect = fitz.Rect(text_block.block_bbox)
                                
                                # 检查当前块是否包含在blocks级别块中
                                if block_info_rect.contains(fitz.Point(current_center_x, current_center_y)):
                                    # 计算重叠面积
                                    intersection = block_info_rect.intersect(fitz.Rect(block_x0, block_y0, block_x1, block_y1))
                                    overlap_area = intersection.width * intersection.height
                                    
                                    if overlap_area > max_overlap:
                                        max_overlap = overlap_area
                                        matched_block_no = block_no
                            
                            # 如果没有找到包含中心点的块，尝试使用重叠面积最大的块
                            if matched_block_no is None:
                                for block_no, text_block in text_block_objects.items():
                                    block_info_rect = fitz.Rect(text_block.block_bbox)
                                    intersection = block_info_rect.intersect(fitz.Rect(block_x0, block_y0, block_x1, block_y1))
                                    overlap_area = intersection.width * intersection.height
                                    
                                    if overlap_area > max_overlap:
                                        max_overlap = overlap_area
                                        matched_block_no = block_no
                            
                            if matched_block_no is not None:
                                # 遍历块内的行
                                for line in block.get("lines", []):
                                    # 遍历行内的span（包含相同属性的文本）
                                    for span in line.get("spans", []):
                                        # 提取详细属性
                                        font = span.get("font", "")
                                        size = span.get("size", 10)
                                        color = span.get("color", 0)
                                        flags = span.get("flags", 0)
                                        
                                        # 更新TextBlock对象的样式信息
                                        text_block_objects[matched_block_no].update_style(
                                            font=font,
                                            font_size=size,
                                            color=color,
                                            flags=flags
                                        )
                                        logger.debug(f"更新块 {matched_block_no} 的样式信息: 字体='{font}', 大小={size}, 颜色={color}, flags={flags}")
                    
                    # 3. 按垂直位置排序TextBlock对象
                    sorted_text_blocks = sorted(
                        text_block_objects.values(),
                        key=lambda block: block.block_bbox[1]  # 按y0（顶部位置）排序
                    )
                    
                    # 直接添加TextBlock对象到结果
                    result['pages'].append({
                        'page_num': page_num + 1,
                        'text_blocks': sorted_text_blocks
                    })
                    
                    # 日志记录
                    logger.info(f"第{page_num + 1}页: 提取到{len(sorted_text_blocks)}个文本块")
                    for i, text_block in enumerate(sorted_text_blocks):
                        logger.info(f"第{page_num + 1}页 文本块 {i+1}: '{text_block.block_text}' 位置: {text_block.block_bbox} 块编号: {text_block.block_no} 字体: {text_block.font} 大小: {text_block.font_size} 粗体: {text_block.bold} 斜体: {text_block.italic}")
            
            # 使用pdfplumber提取表格
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 提取表格
                    tables = page.extract_tables()
                    
                    if tables:
                        for table_idx, table in enumerate(tables):
                            # 过滤掉空表格
                            if any(row for row in table):
                                result['tables'].append({
                                    'page_num': page_num + 1,
                                    'table_idx': table_idx,
                                    'content': table
                                })
                                logger.info(f"表格: 第{page_num + 1}页-表格{table_idx}, 包含{len(table)}行{len(table[0]) if table else 0}列")
            
            # 计算总文本块数
            total_text_blocks = sum(len(page['text_blocks']) for page in result['pages'])
            logger.info(f"提取完成: 总文本块={total_text_blocks}, 总表格={len(result['tables'])}")
            
            # 创建PdfPage对象列表
            pdf_pages = []
            for page_dict in result['pages']:
                pdf_page = PdfPage(
                    page_num=page_dict['page_num'],
                    text_blocks=page_dict['text_blocks']
                )
                pdf_pages.append(pdf_page)
            
            # 创建PdfTable对象列表
            pdf_tables = []
            for table_dict in result['tables']:
                pdf_table = PdfTable(
                    page_num=table_dict['page_num'],
                    table_idx=table_dict['table_idx'],
                    content=table_dict['content']
                )
                pdf_tables.append(pdf_table)
            
            # 创建并返回PdfExtraction对象
            return PdfExtraction(
                total_pages=result['total_pages'],
                pages=pdf_pages,
                tables=pdf_tables
            )
            
        except Exception as e:
            logger.error(f"提取PDF文本时出错: {str(e)}", exc_info=True)
            raise Exception(f"提取PDF文本时出错: {str(e)}")
    
    def extract_page_text(self, pdf_path, page_num):
        """提取指定页面的文本内容
        
        Args:
            pdf_path (str): PDF文件路径
            page_num (int): 页码（从1开始）
            
        Returns:
            PdfPage: 包含指定页面文本内容的对象
                - page_num (int): 页码
                - text_blocks (list[TextBlock]): 文本块列表，按垂直位置从上到下排序
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        logger.info(f"开始提取页面文本: {pdf_path}, 页码={page_num}")
        
        with fitz.open(pdf_path) as doc:
            if page_num < 1 or page_num > len(doc):
                raise ValueError(f"页码超出范围: {page_num}，总页数: {len(doc)}")
            
            page = doc[page_num - 1]
            
            # 1. 提取完整文本块（blocks级别）
            blocks = page.get_text("blocks", flags=1)
            
            # 创建TextBlock对象字典，用于存储每个块的完整信息
            text_block_objects = {}
            
            # 过滤非文本块，仅保留有效文本块并创建TextBlock对象
            for block in blocks:
                x0, y0, x1, y1, text, block_no, block_type = block
                if block_type == 0 and text.strip():
                    # 创建TextBlock对象
                    text_block = TextBlock(
                        block_no=block_no,
                        text=text,
                        bbox=(x0, y0, x1, y1),
                        block_type=block_type
                    )
                    text_block_objects[block_no] = text_block
            
            # 2. 使用dict模式提取详细文本信息，包括字体属性
            text_dict = page.get_text("dict", flags=1)
            
            # 更新TextBlock对象的样式信息
            for block in text_dict.get("blocks", []):
                if block["type"] == 0:  # 文本块
                    block_x0 = block["bbox"][0]
                    block_y0 = block["bbox"][1]
                    block_x1 = block["bbox"][2]
                    block_y1 = block["bbox"][3]
                    
                    # 计算当前块的中心点
                    current_center_x = (block_x0 + block_x1) / 2
                    current_center_y = (block_y0 + block_y1) / 2
                    
                    # 查找最匹配的blocks级别块编号
                    matched_block_no = None
                    max_overlap = 0
                    
                    for block_no, text_block in text_block_objects.items():
                        block_info_rect = fitz.Rect(text_block.block_bbox)
                        
                        # 检查当前块是否包含在blocks级别块中
                        if block_info_rect.contains(fitz.Point(current_center_x, current_center_y)):
                            # 计算重叠面积
                            intersection = block_info_rect.intersect(fitz.Rect(block_x0, block_y0, block_x1, block_y1))
                            overlap_area = intersection.width * intersection.height
                            
                            if overlap_area > max_overlap:
                                max_overlap = overlap_area
                                matched_block_no = block_no
                    
                    # 如果没有找到包含中心点的块，尝试使用重叠面积最大的块
                    if matched_block_no is None:
                        for block_no, text_block in text_block_objects.items():
                            block_info_rect = fitz.Rect(text_block.block_bbox)
                            intersection = block_info_rect.intersect(fitz.Rect(block_x0, block_y0, block_x1, block_y1))
                            overlap_area = intersection.width * intersection.height
                            
                            if overlap_area > max_overlap:
                                max_overlap = overlap_area
                                matched_block_no = block_no
                    
                    if matched_block_no is not None:
                        # 遍历块内的行
                        for line in block.get("lines", []):
                            # 遍历行内的span（包含相同属性的文本）
                            for span in line.get("spans", []):
                                # 提取详细属性
                                font = span.get("font", "")
                                size = span.get("size", 10)
                                color = span.get("color", 0)
                                flags = span.get("flags", 0)
                                
                                # 更新TextBlock对象的样式信息
                                text_block_objects[matched_block_no].update_style(
                                    font=font,
                                    font_size=size,
                                    color=color,
                                    flags=flags
                                )
                                logger.debug(f"更新块 {matched_block_no} 的样式信息: 字体='{font}', 大小={size}, 颜色={color}, flags={flags}")
            
            # 3. 按垂直位置排序TextBlock对象
            sorted_text_blocks = sorted(
                text_block_objects.values(),
                key=lambda block: block.block_bbox[1]  # 按y0（顶部位置）排序
            )
            
            # 创建并返回PdfPage对象
            pdf_page = PdfPage(
                page_num=page_num,
                text_blocks=sorted_text_blocks
            )
            
            logger.info(f"页面{page_num}提取完成: 共{len(sorted_text_blocks)}个文本块")
            for i, text_block in enumerate(sorted_text_blocks):
                logger.info(f"第{page_num}页 文本块 {i+1}: '{text_block.block_text}' 位置: {text_block.block_bbox} 块编号: {text_block.block_no} 字体: {text_block.font} 大小: {text_block.font_size} 粗体: {text_block.bold} 斜体: {text_block.italic}")
            
            return pdf_page
    
    def extract_tables(self, pdf_path):
        """仅提取PDF中的表格内容
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            list[PdfTable]: 提取的表格列表
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        logger.info(f"开始提取表格: {pdf_path}")
        
        pdf_tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    if page_tables:
                        for table_idx, table in enumerate(page_tables):
                            if any(row for row in table):
                                # 创建PdfTable对象
                                pdf_table = PdfTable(
                                    page_num=page_num + 1,
                                    table_idx=table_idx,
                                    content=table
                                )
                                pdf_tables.append(pdf_table)
                                logger.info(f"表格: 第{page_num + 1}页-表格{table_idx}, 包含{len(table)}行{len(table[0]) if table else 0}列")
            
            logger.info(f"表格提取完成: 共{len(pdf_tables)}个表格")
            return pdf_tables
            
        except Exception as e:
            raise Exception(f"提取表格时出错: {str(e)}")
    
    def extract_text_blocks(self, pdf_path):
        """提取PDF中每个文本块的完整文本和位置
        
        确保文段完整性，适合整体翻译
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            PdfExtraction: 包含提取的文本块信息
                - total_pages (int): PDF总页数
                - pages (list[PdfPage]): 每页的文本块列表
                    - page_num (int): 页码
                    - text_blocks (list[TextBlock]): 文本块列表，按垂直位置从上到下排序
                - tables (list[PdfTable]): 提取的表格列表（此方法返回空列表）
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        result = {
            'total_pages': 0,
            'pages': []
        }
        
        try:
            logger.info(f"开始提取文本块: {pdf_path}")
            
            with fitz.open(pdf_path) as doc:
                result['total_pages'] = len(doc)
                logger.info(f"PDF总页数: {len(doc)}")
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # 1. 提取完整文本块（blocks级别）
                    blocks = page.get_text("blocks", flags=1)
                    
                    # 创建TextBlock对象列表
                    text_block_objects = []
                    
                    # 过滤非文本块，仅保留有效文本块并创建TextBlock对象
                    for block in blocks:
                        x0, y0, x1, y1, text, block_no, block_type = block
                        if block_type == 0 and text.strip():
                            # 创建TextBlock对象
                            text_block = TextBlock(
                                block_no=block_no,
                                text=text,
                                bbox=(x0, y0, x1, y1),
                                block_type=block_type
                            )
                            text_block_objects.append(text_block)
                    
                    # 2. 使用dict模式提取详细文本信息，包括字体属性
                    text_dict = page.get_text("dict", flags=1)
                    
                    # 更新TextBlock对象的样式信息
                    for block in text_dict.get("blocks", []):
                        if block["type"] == 0:  # 文本块
                            block_x0 = block["bbox"][0]
                            block_y0 = block["bbox"][1]
                            block_x1 = block["bbox"][2]
                            block_y1 = block["bbox"][3]
                            
                            # 计算当前块的中心点
                            current_center_x = (block_x0 + block_x1) / 2
                            current_center_y = (block_y0 + block_y1) / 2
                            
                            # 查找最匹配的blocks级别块编号
                            matched_block = None
                            max_overlap = 0
                            
                            for text_block in text_block_objects:
                                block_info_rect = fitz.Rect(text_block.block_bbox)
                                
                                # 检查当前块是否包含在blocks级别块中
                                if block_info_rect.contains(fitz.Point(current_center_x, current_center_y)):
                                    # 计算重叠面积
                                    intersection = block_info_rect.intersect(fitz.Rect(block_x0, block_y0, block_x1, block_y1))
                                    overlap_area = intersection.width * intersection.height
                                    
                                    if overlap_area > max_overlap:
                                        max_overlap = overlap_area
                                        matched_block = text_block
                            
                            # 如果没有找到包含中心点的块，尝试使用重叠面积最大的块
                            if matched_block is None:
                                for text_block in text_block_objects:
                                    block_info_rect = fitz.Rect(text_block.block_bbox)
                                    intersection = block_info_rect.intersect(fitz.Rect(block_x0, block_y0, block_x1, block_y1))
                                    overlap_area = intersection.width * intersection.height
                                    
                                    if overlap_area > max_overlap:
                                        max_overlap = overlap_area
                                        matched_block = text_block
                            
                            if matched_block is not None:
                                # 遍历块内的行
                                for line in block.get("lines", []):
                                    # 遍历行内的span（包含相同属性的文本）
                                    for span in line.get("spans", []):
                                        # 提取详细属性
                                        font = span.get("font", "")
                                        size = span.get("size", 10)
                                        color = span.get("color", 0)
                                        flags = span.get("flags", 0)
                                        
                                        # 更新TextBlock对象的样式信息
                                        matched_block.update_style(
                                            font=font,
                                            font_size=size,
                                            color=color,
                                            flags=flags
                                        )
                                        logger.debug(f"更新块 {matched_block.block_no} 的样式信息: 字体='{font}', 大小={size}, 颜色={color}, flags={flags}")
                    
                    # 3. 按垂直位置排序TextBlock对象
                    sorted_text_blocks = sorted(
                        text_block_objects,
                        key=lambda block: block.block_bbox[1]  # 按y0（顶部位置）排序
                    )
                    
                    # 创建PdfPage对象
                    pdf_page = PdfPage(
                        page_num=page_num + 1,
                        text_blocks=sorted_text_blocks
                    )
                    # 添加到结果
                    result['pages'].append(pdf_page)
                    logger.info(f"第{page_num + 1}页: 提取到{len(sorted_text_blocks)}个文本块")
            
            logger.info(f"提取文本块完成，总页数: {result['total_pages']}")
            
            # 创建并返回PdfExtraction对象
            return PdfExtraction(
                total_pages=result['total_pages'],
                pages=result['pages'],
                tables=[]  # extract_text_blocks方法不提取表格，返回空列表
            )
        
        except Exception as e:
            logger.error(f"提取文本块时出错: {str(e)}", exc_info=True)
            raise Exception(f"提取文本块时出错: {str(e)}")
    
    def get_metadata(self, pdf_path):
        """获取PDF文件的元数据
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            dict: PDF元数据字典
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        logger.info(f"获取PDF元数据: {pdf_path}")
        
        try:
            with fitz.open(pdf_path) as doc:
                metadata = doc.metadata
                result_metadata = {
                    'title': metadata.get('title', ''),
                    'author': metadata.get('author', ''),
                    'subject': metadata.get('subject', ''),
                    'keywords': metadata.get('keywords', ''),
                    'creator': metadata.get('creator', ''),
                    'producer': metadata.get('producer', ''),
                    'creation_date': metadata.get('creationDate', ''),
                    'modification_date': metadata.get('modDate', ''),
                    'total_pages': len(doc)
                }
                logger.info(f"PDF元数据: 标题=\"{result_metadata['title']}\", 作者=\"{result_metadata['author']}\", 总页数={result_metadata['total_pages']}")
                return result_metadata
                
        except Exception as e:
            raise Exception(f"获取PDF元数据时出错: {str(e)}")

# 创建PdfExtractor实例
pdf_extractor = PdfExtractor()
