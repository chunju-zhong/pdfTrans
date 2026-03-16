import fitz  # PyMuPDF
import os
import logging
from models.text_block import TextBlock
from models.extraction import PdfPage, PdfTable, PdfImage, PdfExtraction
from .extractors import (
    extract_tables_by_camelot,
    extract_tables_by_pymupdf,
    mark_non_body_text,
    process_page_numbers,
    analyze_text_block_style,
    update_text_block_style
)
from .chapter_identifier import ChapterIdentifier

logger = logging.getLogger(__name__)


class PdfExtractor:
    """PDF文本提取类
    
    负责从PDF文件中提取文本内容，包括普通文本和表格内容，并保留文本的位置信息。
    """
    
    def __init__(self, pdf_path=None, table_extractor='pymupdf'):
        """初始化PdfExtractor对象

        Args:
            pdf_path (str, optional): PDF文件路径. Defaults to None.
            table_extractor (str, optional): 表格提取器类型，可选值: 'pymupdf' 或 'camelot'. Defaults to 'pymupdf'.
        """
        self.pdf_path = pdf_path
        self.metadata = None
        self.total_pages = 0
        self.chapter_identifier = ChapterIdentifier()
        self.table_extractor = table_extractor
        
        if pdf_path:
            self.metadata = self.get_metadata()
            self.total_pages = self.metadata.get('total_pages', 0)
    
    def extract_tables(self, pages=None):
        """提取PDF中的表格内容，可以指定页面

        Args:
            pages (list[int] | None): 指定要提取的页码列表（从1开始），None表示提取所有页面
            
        Returns:
            tuple[list[PdfTable], dict]: 包含提取的表格列表和按页码组织的表格边界框字典
                - list[PdfTable]: 提取的表格列表
                - dict: 按页码组织的表格边界框字典，键为页码，值为边界框列表
        """
        if not self.pdf_path:
            raise ValueError("PDF文件路径不能为空")
        
        # 根据table_extractor选择使用哪种表格提取方法
        if self.table_extractor == 'camelot':
            logger.info("使用Camelot提取表格")
            return extract_tables_by_camelot(self.pdf_path, pages)
        else:
            logger.info("使用PyMuPDF提取表格")
            return extract_tables_by_pymupdf(self.pdf_path, pages)
    
    def get_metadata(self):
        """提取PDF的元数据信息

        Returns:
            dict: 包含PDF元数据的字典
        """
        if not self.pdf_path:
            raise ValueError("PDF文件路径不能为空")
        
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")
        
        try:
            logger.info(f"开始提取PDF元数据: {self.pdf_path}")
            
            with fitz.open(self.pdf_path) as doc:
                metadata = doc.metadata
                # 添加总页数信息
                metadata['total_pages'] = len(doc)
                # 确保包含creation_date键（与creationDate保持一致）
                if 'creationDate' in metadata and 'creation_date' not in metadata:
                    metadata['creation_date'] = metadata['creationDate']
                # 确保包含modification_date键（与modDate保持一致）
                if 'modDate' in metadata and 'modification_date' not in metadata:
                    metadata['modification_date'] = metadata['modDate']
                logger.info(f"PDF元数据提取完成: {metadata}")
                return metadata
                
        except Exception as e:
            logger.error(f"提取PDF元数据时出错: {str(e)}", exc_info=True)
            raise Exception(f"提取PDF元数据时出错: {str(e)}")
    
    def get_chapters(self):
        """获取PDF文档的章节信息

        Returns:
            list: 章节列表
        """
        return self.chapter_identifier.get_chapters()
    
    def has_chapters(self):
        """检查PDF文档是否有章节信息

        Returns:
            bool: 是否有章节信息
        """
        return self.chapter_identifier.has_chapters()
    
    def extract(self, pages=None, mark_non_body=True, extract_chapter=True):
        """提取PDF中的文本内容，可以指定页面

        Args:
            pages (list[int] | None): 指定要提取的页码列表（从1开始），None表示提取所有页面
            mark_non_body (bool): 是否标记非正文文本块（页眉、页脚、页码），默认为True
            extract_chapter (bool): 是否提取章节信息，默认为True  
            
        Returns:
            PdfExtraction: 包含提取的文本内容和元数据的对象
                - total_pages (int): PDF总页数
                - pages (list[PdfPage]): 每页的文本内容列表
                    - page_num (int): 页码
                    - text_blocks (list[TextBlock]): 文本块列表，按垂直位置从上到下排序
                - tables (list[PdfTable]): 提取的表格列表
        """
        logger.info(f"PdfExtractor.extract方法接收到的extract_chapter值: {extract_chapter}")
        if not self.pdf_path:
            raise ValueError("PDF文件路径不能为空")
        
        # 检查文件是否存在
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")
        
        # 存储页面尺寸信息
        page_sizes = {}
        
        # 创建临时图像目录
        temp_images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp_images')
        os.makedirs(temp_images_dir, exist_ok=True)
        
        # 直接创建PdfExtraction所需的对象列表
        pdf_pages = []
        pdf_images = []
        total_pages = self.total_pages
        
        try:
            logger.info(f"开始提取PDF: {self.pdf_path}")
            
            # 提取章节信息
            logger.info("重置章节信息")
            self.chapter_identifier.reset()
            if extract_chapter:
                self.chapter_identifier.extract_bookmarks(self.pdf_path)
                logger.info("已提取章节信息")
            
            # 先提取表格
            pdf_tables, page_tables = self.extract_tables(pages)
            
            # 使用PyMuPDF提取普通文本和页面尺寸
            with fitz.open(self.pdf_path) as doc:
                if not total_pages:
                    total_pages = len(doc)
                    logger.info(f"PDF总页数: {total_pages}")
                
                # 处理页码参数
                _, zero_based_pages = process_page_numbers(pages, total_pages)
                
                for page_num in zero_based_pages:
                    current_page_num = page_num + 1
                    page = doc[page_num]
                    
                    # 处理单个页面
                    page_result = self._process_page(
                        page=page,
                        current_page_num=current_page_num,
                        page_tables=page_tables,
                        temp_images_dir=temp_images_dir
                    )
                    
                    if page_result:
                        pdf_page, page_images, page_size = page_result
                        pdf_pages.append(pdf_page)
                        pdf_images.extend(page_images)
                        page_sizes[current_page_num] = page_size
            
            # 完成提取过程
            extraction_result = self._finalize_extraction(
                pdf_pages=pdf_pages,
                pdf_images=pdf_images,
                pdf_tables=pdf_tables,
                page_sizes=page_sizes,
                total_pages=total_pages,
                mark_non_body=mark_non_body
            )
            
            # 关联表格和图像到章节（文本块已在_process_page中按页关联）
            if self.chapter_identifier.has_chapters():
                # 关联表格
                if extraction_result.tables:
                    self.chapter_identifier.associate_tables(extraction_result.tables)
                
                # 关联图像
                if extraction_result.images:
                    self.chapter_identifier.associate_images(extraction_result.images)
            
            return extraction_result
            
        except Exception as e:
            logger.error(f"提取PDF文本时出错: {str(e)}", exc_info=True)
            raise Exception(f"提取PDF文本时出错: {str(e)}")
    
    def _process_page(self, page, current_page_num, page_tables, temp_images_dir):
        """处理单个页面
        
        Args:
            page: PyMuPDF页面对象
            current_page_num (int): 当前页码（1-based）
            page_tables (dict): 按页码组织的表格边界框字典
            temp_images_dir (str): 临时图像目录路径
            
        Returns:
            tuple: (PdfPage, list[PdfImage], tuple) 或 None
        """
        try:
            # 获取页面实际尺寸
            page_rect = page.rect
            page_size = (page_rect.width, page_rect.height)
            logger.debug(f"页面{current_page_num} 实际尺寸: {page_rect}")
            
            # 获取当前页的表格边界框
            current_page_tables = page_tables.get(current_page_num, [])
            
            # 提取文本块
            text_block_objects = self._extract_text_blocks(
                page=page,
                current_page_num=current_page_num,
                current_page_tables=current_page_tables
            )
            
            # 提取图像
            page_images = self._extract_images(
                page=page,
                current_page_num=current_page_num,
                temp_images_dir=temp_images_dir
            )
            
            # 创建PdfPage对象
            pdf_page = self._create_pdf_page(
                current_page_num=current_page_num,
                text_block_objects=text_block_objects
            )
            
            return pdf_page, page_images, page_size
        except Exception as e:
            logger.error(f"处理页面{current_page_num}时出错: {str(e)}")
            return None
    
    def _extract_text_blocks(self, page, current_page_num, current_page_tables):
        """从页面中提取文本块
        
        Args:
            page: PyMuPDF页面对象
            current_page_num (int): 当前页码（1-based）
            current_page_tables (list): 当前页的表格边界框列表
            
        Returns:
            dict: 文本块对象字典
        """
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
                # 检查文本块是否与表格边界框重叠
                is_table_text = False
                block_rect = fitz.Rect(x0, y0, x1, y1)
                block_area = block_rect.width * block_rect.height
                
                if current_page_tables:
                    for table_bbox in current_page_tables:
                        table_rect = fitz.Rect(table_bbox)
                        # 计算重叠面积
                        intersection = block_rect.intersect(table_rect)
                        overlap_area = intersection.width * intersection.height
                        
                        # 如果重叠面积超过文本块面积的50%，则视为表格文本
                        if overlap_area > block_area * 0.5:
                            is_table_text = True
                            logger.debug(f"页面{current_page_num} 文本块 {block_no} 与表格重叠，视为表格文本，跳过")
                            break
                
                # 如果不是表格文本，创建TextBlock对象
                if not is_table_text:
                    text_block = TextBlock(
                        block_no=block_no,
                        text=text,
                        bbox=(x0, y0, x1, y1),
                        block_type=block_type,
                        page_num=current_page_num
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
                    # 分析文本块样式
                    style_info = analyze_text_block_style((block_x0, block_y0, block_x1, block_y1, "", matched_block_no, 0), text_dict)
                    if style_info:
                        # 使用样式信息更新TextBlock对象
                        update_text_block_style(text_block_objects[matched_block_no], style_info)
        
        return text_block_objects
    
    def _extract_images(self, page, current_page_num, temp_images_dir):
        """从页面中提取图像
        
        Args:
            page: PyMuPDF页面对象
            current_page_num (int): 当前页码（1-based）
            temp_images_dir (str): 临时图像目录路径
            
        Returns:
            list[PdfImage]: 提取的图像列表
        """
        page_images = []
        
        # 提取图像
        images = page.get_images(full=True)
        for image_idx, img in enumerate(images):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image['image']
                image_ext = base_image['ext']
                image_path = os.path.join(temp_images_dir, f'page_{current_page_num}_image_{image_idx}.{image_ext}')
                
                # 保存图像
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                
                # 获取图像实际边界框
                image_rects = page.get_image_rects(xref)
                if image_rects:
                    # 使用第一个边界框（通常每个图像只有一个边界框）
                    rect = image_rects[0]
                    bbox = (rect.x0, rect.y0, rect.x1, rect.y1)
                    logger.info(f"获取图像边界框: {bbox}")
                else:
                    # 如果没有获取到边界框，使用默认值
                    bbox = (0, 0, 100, 100)
                    logger.warning(f"无法获取图像边界框，使用默认值: {bbox}")
                
                # 验证边界框格式
                if len(bbox) == 4 and bbox[1] < bbox[3]:
                    # 边界框格式正确
                    pass
                else:
                    # 边界框格式异常，使用默认值
                    logger.warning(f"图像边界框格式异常: {bbox}，使用默认值")
                    bbox = (0, 0, 100, 100)
                
                # 直接创建PdfImage对象并添加到列表
                pdf_image = PdfImage(
                    page_num=current_page_num,
                    image_idx=image_idx,
                    image_path=image_path,
                    bbox=bbox
                )
                page_images.append(pdf_image)
                logger.info(f"提取图像: 第{current_page_num}页-图像{image_idx}, 保存到: {image_path}, 边界框: {bbox}, 位置: x0={bbox[0]}, y0={bbox[1]}, x1={bbox[2]}, y1={bbox[3]}")
            except Exception as e:
                logger.error(f"提取图像时出错: {str(e)}")
        
        return page_images
    
    def _create_pdf_page(self, current_page_num, text_block_objects):
        """创建PdfPage对象
        
        Args:
            current_page_num (int): 当前页码（1-based）
            text_block_objects (dict): 文本块对象字典
            
        Returns:
            PdfPage: PdfPage对象
        """
        # 按垂直位置排序TextBlock对象
        sorted_text_blocks = sorted(
            text_block_objects.values(),
            key=lambda block: block.block_bbox[1]  # 按y0（顶部位置）排序
        )
        
        if self.chapter_identifier.has_chapters():
            self.chapter_identifier.associate_text_blocks(sorted_text_blocks)
        
        # 创建PdfPage对象
        pdf_page = PdfPage(
            page_num=current_page_num,
            text_blocks=sorted_text_blocks
        )
        
        return pdf_page
    
    def _finalize_extraction(self, pdf_pages, pdf_images, pdf_tables, page_sizes, total_pages, mark_non_body=True):
        """完成提取过程
        
        Args:
            pdf_pages (list[PdfPage]): 页面列表
            pdf_images (list[PdfImage]): 图像列表
            pdf_tables (list[PdfTable]): 表格列表
            page_sizes (dict): 页面尺寸字典
            total_pages (int): 总页数
            mark_non_body (bool): 是否标记非正文文本块，默认为True
            
        Returns:
            PdfExtraction: 提取结果对象
        """
        # 计算总文本块数
        total_text_blocks = sum(len(page.text_blocks) for page in pdf_pages)
        logger.info(f"提取完成: 总文本块={total_text_blocks}, 总表格={len(pdf_tables)}")
        
        # 标记非正文文本块（页眉、页脚、页码）
        mark_non_body_text(pdf_pages, page_sizes, mark_non_body)
        
        # 日志记录 - 移到标记非正文文本块之后
        for pdf_page in pdf_pages:
            logger.info(f"第{pdf_page.page_num}页: 提取到{len(pdf_page.text_blocks)}个文本块")
            for i, text_block in enumerate(pdf_page.text_blocks):
                logger.info(f"第{pdf_page.page_num}页 文本块 {i+1}: '{text_block.block_text}' 位置: {text_block.block_bbox} 块编号: {text_block.block_no} 字体: {text_block.font} 大小: {text_block.font_size} 粗体: {text_block.bold} 斜体: {text_block.italic} 是否为正文: {text_block.is_body_text}")
        
        # 直接创建并返回PdfExtraction对象
        return PdfExtraction(
            total_pages=total_pages,
            pages=pdf_pages,
            tables=pdf_tables,
            images=pdf_images
        )
    



