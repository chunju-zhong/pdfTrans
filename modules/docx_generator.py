import os
import logging
from docx import Document
from docx.shared import Inches, RGBColor, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)

class DocxGenerator:
    """Word生成器类
    
    负责将翻译后的文本生成Word文档，支持文本、表格和图像的生成。
    """
    
    def __init__(self):
        """初始化DocxGenerator对象"""
        logger.info("Word生成器初始化完成")
    
    def _clean_xml_compatible_text(self, text):
        """清理文本，确保它只包含XML兼容的字符
        
        Args:
            text (str): 要清理的文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 移除NULL字节和控制字符（保留制表符、换行符和回车符）
        cleaned_text = ""
        for char in text:
            char_code = ord(char)
            # 保留XML兼容的字符：
            # 1. 可打印的ASCII字符（32-126）
            # 2. 制表符（9）、换行符（10）、回车符（13）
            # 3. Unicode字符（128+）
            if (32 <= char_code <= 126) or char_code in (9, 10, 13) or char_code >= 128:
                cleaned_text += char
        
        return cleaned_text
    
    def generate_docx(self, translated_content, images, output_docx_path, target_lang="zh"):
        """生成翻译后的Word文档
        
        Args:
            translated_content (dict): 翻译后的内容
                - blocks (list): 每页的完整文本块列表 (翻译后的文本块)
                    - page_num (int): 页码
                    - text_blocks (list): TextBlock对象列表
                        - block_text (str): 完整文本块内容 (已翻译)
                        - block_bbox (tuple): 文本块位置 (x0, y0, x1, y1)
                        - block_no (int): 块编号
                        - block_type (int): 块类型
                        - font (str): 字体名称
                        - font_size (float): 字体大小
                        - color (int): 颜色值
                        - flags (int): 样式标记
                - merged_translations (list): 合并后的翻译结果
                    - text (str): 合并后的翻译文本
                    - page_num (int): 页码
                    - font (str): 字体名称
                    - font_size (float): 字体大小
                    - color (int): 颜色值
                    - bold (bool): 是否粗体
                    - italic (bool): 是否斜体
                - tables (list): 翻译后的表格列表
            images (list): 图像信息列表
                - page_num (int): 页码
                - image_idx (int): 图像索引
                - image_path (str): 图像路径
                - bbox (tuple): 图像位置
            output_docx_path (str): 输出Word文件路径
            target_lang (str): 目标语言代码
        """
        logger.info(f"开始生成Word文档，输出文件: {output_docx_path}, 目标语言: {target_lang}")
        
        try:
            # 创建新的Word文档
            doc = Document()
            logger.info("创建Word文档成功")
            
            # 使用合并后的翻译结果生成Word文档
            logger.info("使用合并后的翻译结果生成Word文档")
            # 按页码组织合并后的翻译结果
            merged_by_page = {}
            for item in translated_content.get('merged_translations', []):
                page_num = item['page_num']
                if page_num not in merged_by_page:
                    merged_by_page[page_num] = []
                merged_by_page[page_num].append(item)
            
            # 按页码组织图像
            images_by_page = {}
            for image in images:
                page_num = image.page_num
                if page_num not in images_by_page:
                    images_by_page[page_num] = []
                images_by_page[page_num].append(image)
            
            # 获取所有页码的列表
            sorted_pages = sorted(merged_by_page.keys())
            # 处理每页内容
            for i, page_num in enumerate(sorted_pages):
                logger.info(f"处理第 {page_num} 页")
                
                # 添加合并后的文本块
                for item in merged_by_page[page_num]:
                    self._add_merged_text(doc, item)
                
                # 添加图像
                page_images = images_by_page.get(page_num, [])
                for image in page_images:
                    self._add_image(doc, image)
                
                # 只在不是最后一页时添加分页符
                if i < len(sorted_pages) - 1:
                    # 添加分页符
                    doc.add_page_break()
            
            # 处理表格
            if 'tables' in translated_content:
                for table in translated_content['tables']:
                    self._add_table(doc, table)
            
            # 保存文档
            output_dir = os.path.dirname(output_docx_path)
            os.makedirs(output_dir, exist_ok=True)
            
            doc.save(output_docx_path)
            logger.info(f"Word文档生成完成，输出文件: {output_docx_path}")
            
        except Exception as e:
            logger.error(f"生成Word文档时出错: {str(e)}", exc_info=True)
            raise Exception(f"生成Word文档时出错: {str(e)}")
    
    def _add_merged_text(self, doc, merged_item):
        """添加合并后的文本到Word文档
        
        Args:
            doc: Word文档对象
            merged_item: 合并后的文本项
                - text (str): 合并后的翻译文本
                - font (str): 字体名称
                - font_size (float): 字体大小
                - color (int): 颜色值
                - bold (bool): 是否粗体
                - italic (bool): 是否斜体
        """
        # 创建段落
        paragraph = doc.add_paragraph()
        
        # 清理文本，确保它只包含XML兼容的字符
        cleaned_text = self._clean_xml_compatible_text(merged_item['text'])
        
        # 添加文本
        run = paragraph.add_run(cleaned_text)
        
        # 应用样式
        try:
            # 设置字体
            run.font.name = merged_item['font']
            
            # 设置字体大小
            font_size = merged_item['font_size']
            run.font.size = Pt(font_size)
            logger.info(f"应用字体大小: {font_size} 到文本: '{cleaned_text[:50]}...'")
            
            # 设置颜色
            color = merged_item['color']
            if color > 0xFFFFFF:  # ARGB
                r = (color >> 16) & 0xFF
                g = (color >> 8) & 0xFF
                b = color & 0xFF
            else:  # RGB
                r = (color >> 16) & 0xFF
                g = (color >> 8) & 0xFF
                b = color & 0xFF
            run.font.color.rgb = RGBColor(r, g, b)
            
            # 设置粗体和斜体
            run.bold = merged_item['bold']
            run.italic = merged_item['italic']
            
            logger.debug(f"添加合并文本，内容: '{cleaned_text[:50]}...'，字体: {merged_item['font']}，大小: {font_size}")
        except Exception as e:
            logger.warning(f"设置合并文本样式失败: {e}")
    
    def _add_text_block(self, doc, text_block):
        """添加文本块到Word文档
        
        Args:
            doc: Word文档对象
            text_block: 文本块对象
        """
        # 创建段落
        paragraph = doc.add_paragraph()
        
        # 清理文本，确保它只包含XML兼容的字符
        cleaned_text = self._clean_xml_compatible_text(text_block.block_text)
        
        # 添加文本
        run = paragraph.add_run(cleaned_text)
        
        # 应用样式
        self._apply_style(run, text_block)
        
        logger.debug(f"添加文本块，内容: '{cleaned_text[:50]}...'，字体: {text_block.font}，大小: {text_block.font_size}")
    
    def _apply_style(self, run, text_block):
        """应用样式到文本
        
        Args:
            run: Word文本运行对象
            text_block: 文本块对象
        """
        # 设置字体
        try:
            run.font.name = text_block.font
        except Exception as e:
            logger.warning(f"设置字体失败: {e}，使用默认字体")
        
        # 设置字体大小
        try:
            run.font.size = Pt(text_block.font_size)
        except Exception as e:
            logger.warning(f"设置字体大小失败: {e}")
        
        # 设置颜色
        try:
            color = text_block.color
            if color > 0xFFFFFF:  # ARGB
                r = (color >> 16) & 0xFF
                g = (color >> 8) & 0xFF
                b = color & 0xFF
            else:  # RGB
                r = (color >> 16) & 0xFF
                g = (color >> 8) & 0xFF
                b = color & 0xFF
            run.font.color.rgb = RGBColor(r, g, b)
        except Exception as e:
            logger.warning(f"设置颜色失败: {e}")
        
        # 设置粗体和斜体
        run.bold = text_block.bold
        run.italic = text_block.italic
    
    def _add_image(self, doc, image):
        """添加图像到Word文档
        
        Args:
            doc: Word文档对象
            image: 图像对象
        """
        image_path = image.image_path
        if os.path.exists(image_path):
            try:
                # 计算图像大小（简化处理）
                width = image.bbox[2] - image.bbox[0]
                height = image.bbox[3] - image.bbox[1]
                
                # 转换为英寸（1点 = 1/72英寸）
                width_inch = width / 72
                height_inch = height / 72
                
                # 限制最大尺寸
                max_width = 6.0  # 6英寸
                if width_inch > max_width:
                    ratio = max_width / width_inch
                    width_inch = max_width
                    height_inch = height_inch * ratio
                
                # 添加图像
                doc.add_picture(image_path, width=Inches(width_inch))
                logger.info(f"添加图像成功: {image_path}，尺寸: {width_inch:.2f}x{height_inch:.2f}英寸")
            except Exception as e:
                logger.error(f"添加图像失败: {e}")
        else:
            logger.warning(f"图像文件不存在: {image_path}")
    
    def _add_table(self, doc, table):
        """添加表格到Word文档
        
        Args:
            doc: Word文档对象
            table: 表格对象
        """
        table_data = table.get('cells', [])
        if not table_data:
            logger.warning("表格数据为空，跳过")
            return
        
        # 创建表格
        num_rows = len(table_data)
        num_cols = len(table_data[0]) if num_rows > 0 else 0
        
        if num_rows > 0 and num_cols > 0:
            word_table = doc.add_table(rows=num_rows, cols=num_cols)
            
            # 填充表格数据
            for i, row in enumerate(table_data):
                for j, cell in enumerate(row):
                    # 检查cell类型
                    cell_text = cell.get('text', cell) if isinstance(cell, dict) else cell
                    # 清理文本，确保它只包含XML兼容的字符
                    cleaned_text = self._clean_xml_compatible_text(str(cell_text))
                    word_table.cell(i, j).text = cleaned_text
            
            logger.info(f"添加表格成功，{num_rows}行{num_cols}列")
        else:
            logger.warning("表格数据格式不正确，跳过")