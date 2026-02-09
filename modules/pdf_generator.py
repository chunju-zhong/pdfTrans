import fitz  # PyMuPDF
import os
import sys
import logging
from PIL import ImageFont

# 配置日志
logger = logging.getLogger(__name__)

class PdfGenerator:
    """PDF生成类
    
    负责将翻译后的文本生成新的PDF文件，并尽量保留原始PDF的布局和格式。
    """
    
    def __init__(self):
        """初始化PdfGenerator对象"""
        # 字体目录
        self.fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
        
        # 字体缓存，避免重复加载
        self.font_cache = {}
        
        # 确保字体目录存在
        os.makedirs(self.fonts_dir, exist_ok=True)
        logger.info(f"PDF生成器初始化完成，字体目录: {self.fonts_dir}")
    
    def generate_pdf(self, original_pdf_path, translated_content, output_pdf_path, target_lang="zh"):
        """生成翻译后的PDF文件
        
        Args:
            original_pdf_path (str): 原始PDF文件路径
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
                - tables (list): 翻译后的表格列表
            output_pdf_path (str): 输出PDF文件路径
            target_lang (str): 目标语言代码
        """
        logger.info(f"开始生成PDF，原始文件: {original_pdf_path}, 输出文件: {output_pdf_path}, 目标语言: {target_lang}")
        
        # 添加接收translated_content的日志，记录blocks信息
        logger.info(f"PDF生成器接收到的translated_content包含blocks信息: {('blocks' in translated_content)}")
        if 'blocks' in translated_content:
            total_blocks = sum(len(page.text_blocks) for page in translated_content['blocks'])
            logger.info(f"PDF生成器接收到的blocks信息: 总页数={len(translated_content['blocks'])}, 总blocks数={total_blocks}")
            # 显示所有页面的所有完整块内容
            for i, page_blocks in enumerate(translated_content['blocks']):
                # 直接使用PdfPage对象的text_blocks属性
                blocks_list = page_blocks.text_blocks
                block_count = len(blocks_list)
                logger.debug(f"PDF生成器 第 {i+1} 页有 {block_count} 个文本块")
                for j, block in enumerate(blocks_list):
                    # 直接使用TextBlock对象的属性
                    block_text = block.block_text
                    block_bbox = block.block_bbox
                    block_no = block.block_no
                    logger.debug(f"PDF生成器 第 {i+1} 页 文本块 {j+1}: '{block_text}' 位置: {block_bbox} 块编号: {block_no}")
        else:
            logger.warning(f"PDF生成器未接收到blocks信息，无法绘制翻译文本")
        
        if not os.path.exists(original_pdf_path):
            logger.error(f"原始PDF文件不存在: {original_pdf_path}")
            raise FileNotFoundError(f"原始PDF文件不存在: {original_pdf_path}")
        
        try:
            # 打开原始PDF
            with fitz.open(original_pdf_path) as original_doc:
                logger.info(f"成功打开原始PDF，总页数: {len(original_doc)}")
                
                # 创建新的PDF文档
                new_doc = fitz.open()
                logger.info("创建新的PDF文档成功")
                
                # 记录翻译内容概览
                logger.info(f"翻译内容: 完整文本块 {len(translated_content.get('blocks', []))}, 表格 {len(translated_content.get('tables', []))}")
                
                # 收集有翻译内容的页码
                pages_with_content = set()
                
                # 收集有文本块翻译的页码
                for blocks_content in translated_content.get('blocks', []):
                    pages_with_content.add(blocks_content.page_num)
                
                # 收集有表格翻译的页码
                for table_content in translated_content.get('tables', []):
                    # 使用page_num属性
                    pages_with_content.add(table_content.page_num)
                
                # 将页码转换为原始文档的索引（从0开始）
                pages_to_process = sorted(pages_with_content)
                logger.info(f"需要处理的页码: {pages_to_process}")
                
                # 处理每一页，只处理有翻译内容的页面
                for page_num in pages_to_process:
                    # 转换为原始文档的索引（从0开始）
                    original_page_idx = page_num - 1
                    
                    # 跳过超出范围的页码
                    if original_page_idx < 0 or original_page_idx >= len(original_doc):
                        logger.warning(f"页码 {page_num} 超出原始文档范围，跳过")
                        continue
                    
                    logger.info(f"处理第 {page_num}/{len(pages_to_process)} 页 (原始页码: {page_num})")
                    
                    # 获取原始页面
                    original_page = original_doc[original_page_idx]
                    logger.info(f"原始页面尺寸: {original_page.rect.width}x{original_page.rect.height}")
                    
                    # 克隆原始页面到新文档
                    new_page = new_doc.new_page(width=original_page.rect.width, height=original_page.rect.height)
                    logger.info("创建新页面成功")
                    
                    # 复制原始页面的内容（背景、图像等）
                    new_page.show_pdf_page(new_page.rect, original_doc, original_page_idx)
                    logger.info("复制原始页面内容成功")
                    
                    # 获取当前页的翻译内容
                    page_translated_blocks = None
                    
                    # 获取blocks级别翻译文本
                    for blocks_content in translated_content.get('blocks', []):
                        if blocks_content.page_num == page_num:
                            page_translated_blocks = blocks_content
                            break
                    
                    if page_translated_blocks:
                        blocks_count = len(page_translated_blocks.text_blocks)
                        
                        logger.info(f"第 {page_num} 页有 {blocks_count} 个完整文本块")
                        
                        # 绘制翻译后的文本，直接使用文本块自带的样式信息
                        self._draw_translated_text(new_page, page_translated_blocks, target_lang)
                        logger.info(f"第 {page_num} 页绘制完成")
                    
                    # 处理表格（如果有）
                    page_tables = []
                    for table in translated_content['tables']:
                        # 使用page_num属性
                        if table.page_num == page_num:
                            page_tables.append(table)
                    logger.info(f"第 {page_num} 页有 {len(page_tables)} 个表格需要处理")
                    for i, table in enumerate(page_tables):
                        self._draw_translated_table(new_page, table, target_lang)
                        logger.info(f"第 {page_num} 页表格 {i+1} 绘制完成")
                
                # 如果没有需要处理的页面，生成一个空PDF或显示警告
                if not pages_to_process:
                    logger.warning("没有需要处理的页面，生成空PDF")
                    # 创建一个空白页
                    new_doc.new_page(width=595, height=842)  # A4尺寸
                
                # 保存新PDF
                logger.info(f"开始保存新PDF: {output_pdf_path}")
                
                # 在保存文档之前获取总页数
                total_pages = len(new_doc)
                
                # 保存文档
                new_doc.save(output_pdf_path)
                
                # 关闭文档
                new_doc.close()
                
                # 使用预存的总页数记录日志，避免在文档关闭后访问
                logger.info(f"PDF生成完成，输出文件: {output_pdf_path}, 总页数: {total_pages}")
                
        except Exception as e:
            logger.error(f"生成PDF时出错: {str(e)}", exc_info=True)
            raise Exception(f"生成PDF时出错: {str(e)}")
    
    def _draw_translated_text(self, page, translated_blocks, target_lang="zh"):
        """在页面上绘制翻译后的文本，使用块级关联实现样式保留
        
        核心逻辑：
        1. 直接使用translated_blocks中文本块自带的样式信息
        2. 按原文样式（字体、大小、颜色、位置）渲染翻译文本
        
        Args:
            page (fitz.Page): PDF页面对象
            translated_blocks (PdfPage): 当前页的翻译文本块
                - page_num (int): 页码
                - text_blocks (list): TextBlock对象列表 (已翻译的完整文本块)
            target_lang (str): 目标语言代码
        """
        # 直接使用PdfPage对象的text_blocks属性
        full_text_blocks = translated_blocks.text_blocks
        total_blocks = len(full_text_blocks)
        
        logger.info(f"开始绘制翻译文本V2，共 {total_blocks} 个完整文本块")
        
        # 处理每个完整文本块
        for block_idx, full_block in enumerate(full_text_blocks):
            logger.info(f"处理完整文本块 {block_idx+1}/{total_blocks}")
            
            # 直接使用TextBlock对象的属性
            translated_text = full_block.block_text
            block_bbox = full_block.block_bbox
            
            logger.info(f"翻译文本: '{translated_text}' (共 {len(translated_text)} 字符)")
            logger.info(f"文本块位置: {block_bbox}")
            
            # 直接使用TextBlock对象自带的样式信息
            original_font = full_block.font
            original_font_size = full_block.font_size
            color = full_block.color
            bold = full_block.bold
            italic = full_block.italic
            
            logger.info(f"使用文本块自带样式: 字体='{original_font}', 大小={original_font_size}, 粗体={bold}, 斜体={italic}")
            
            # 修复颜色转换逻辑
            if color > 0xFFFFFF:  # 带alpha通道的ARGB格式 0xAARRGGBB
                r = (color >> 16) & 0xFF
                g = (color >> 8) & 0xFF
                b = color & 0xFF
                logger.debug(f"ARGB颜色: {color:#x} -> R={r}, G={g}, B={b}")
            else:  # 只有RGB值 0xRRGGBB
                r = (color >> 16) & 0xFF
                g = (color >> 8) & 0xFF
                b = color & 0xFF
                logger.debug(f"RGB颜色: {color:#x} -> R={r}, G={g}, B={b}")
            
            # 转换为0-1范围
            rgb_color = (r / 255.0, g / 255.0, b / 255.0)
            logger.debug(f"转换后RGB: {rgb_color}")
            
            # 确保文本颜色不是透明或白色（与背景冲突）
            grayscale = 0.299 * r + 0.587 * g + 0.114 * b
            logger.debug(f"灰度值: {grayscale}")
            
            if grayscale > 200:  # 接近白色，改为黑色
                rgb_color = (0, 0, 0)  # 确保文本可见
                logger.info(f"颜色接近白色，自动改为黑色")
            
            # 获取适合目标语言的字体
            suitable_font = self._get_suitable_font(page, original_font, target_lang)
            logger.info(f"适合的字体: 原字体='{original_font}', 目标语言='{target_lang}', 选择='{suitable_font}'")
            
            # 创建文本框
            rect = fitz.Rect(block_bbox[0], block_bbox[1], block_bbox[2], block_bbox[3])
            logger.debug(f"文本框尺寸: {rect.width}x{rect.height}")
            
            # 绘制背景色覆盖原文
            page.draw_rect(rect, color=(1, 1, 1), fill=True, width=0)
            logger.debug(f"绘制背景色覆盖原文，区域: {rect}")
            
            # 使用默认左对齐
            alignment = 0
            logger.info(f"使用对齐方式: {alignment} (0=左对齐, 1=居中, 2=右对齐)")
            
            # 不再使用字体回退列表，只使用适合的字体
            max_attempts = 5
            success = False
            current_rect = rect
            current_font_size = original_font_size
            
            for attempt in range(1, max_attempts + 1):
                try:
                    # 计算当前尝试的调整策略
                    if attempt <= 3:  # 前3次尝试：调整文本框大小
                        adjusted_font_size = original_font_size
                    else:  # 后2次尝试：调整字体大小
                        reduction_factor = (attempt - 3) * 0.1
                        adjusted_font_size = original_font_size * (1 - reduction_factor)
                        adjusted_font_size = max(adjusted_font_size, original_font_size * 0.7)  # 不小于原大小的70%
                    
                    logger.debug(f"尝试绘制文本，字体: {suitable_font}, 字体大小: {adjusted_font_size}, 文本框: {current_rect}")
                    
                    # 尝试绘制文本
                    result = page.insert_textbox(
                        current_rect,
                        translated_text,
                        fontname=suitable_font,
                        fontsize=adjusted_font_size,
                        color=rgb_color,
                        align=alignment
                    )
                    
                    if result >= 0:
                        logger.info(f"✅ 文本渲染成功，插入了 {result} 个字符，使用字体大小: {adjusted_font_size}，文本框大小: {current_rect}")
                        success = True
                        break
                    
                    # 文本溢出，需要调整
                    logger.warning(f"⚠️  文本溢出，返回值: {result}，当前字体大小: {adjusted_font_size}，文本框: {current_rect}")
                    
                    # 调整文本框大小（仅前3次尝试）
                    if attempt <= 3:
                        # 同时增加高度和宽度
                        new_width = current_rect.width * 1.1
                        new_height = current_rect.height * 1.2
                        logger.debug(f"调整文本框宽度到: {new_width}, 高度到: {new_height}")
                        
                        # 更新文本框
                        current_rect = fitz.Rect(
                            current_rect.x0,
                            current_rect.y0,
                            current_rect.x0 + new_width,
                            current_rect.y0 + new_height
                        )
                except Exception as e:
                    logger.warning(f"❌ 绘制失败: {e}")
                    break
            
            if not success:
                logger.warning(f"所有尝试失败，跳过文本块绘制: '{translated_text[:50]}...'")
        
        logger.info("所有翻译文本绘制完成")
    
    def _get_suitable_font(self, page, original_font, target_lang):
        """获取适合目标语言的字体

        Args:
            page (fitz.Page): PDF页面对象
            original_font (str): 原始字体名称
            target_lang (str): 目标语言代码
            
        Returns:
            str: 适合的字体名称
        
        Raises:
            ValueError: 当找不到适合目标语言的字体时抛出
        """
        logger.info(f"获取适合字体: 原字体='{original_font}', 目标语言='{target_lang}'")
        
        # 1. 检查是否有预先加载的字体
        if original_font:
            try:
                logger.debug(f"尝试使用原始字体 '{original_font}'")
                page.insert_font(fontname=original_font, fontfile=None)
                logger.info(f"成功使用原始字体 '{original_font}'")
                return original_font
            except Exception as e:
                logger.debug(f"原始字体 '{original_font}' 插入失败: {e}")
        
        # 2. 从系统获取可用字体列表
        system_font_paths = self._get_system_fonts()
        
        # 3. 从系统字体中选择支持目标语言的字体
        if system_font_paths:
            logger.info(f"开始从系统字体中选择支持 '{target_lang}' 的字体")
            
            # 特殊处理Arial Unicode.ttf，它支持多种语言
            for font_path in system_font_paths:
                if 'Arial Unicode.ttf' in font_path:
                    try:
                        logger.debug(f"尝试使用Arial Unicode字体: {font_path}")
                        # 使用自定义短名称插入字体
                        fontname = "arialuni"
                        page.insert_font(fontname=fontname, fontfile=font_path)
                        logger.info(f"成功使用Arial Unicode字体")
                        return fontname
                    except Exception as e:
                        logger.debug(f"Arial Unicode字体插入失败: {e}")
                        continue
            
            # 遍历所有系统字体路径
            for font_path in system_font_paths:
                try:
                    # 检查字体是否支持目标语言
                    if self._check_font_support(font_path, target_lang):
                        logger.debug(f"尝试使用系统字体: {font_path}")
                        # 创建自定义短名称，去除空格和特殊字符
                        font_filename = os.path.basename(font_path)
                        fontname = os.path.splitext(font_filename)[0].replace(' ', '_')
                        fontname = ''.join(c for c in fontname if c.isalnum() or c == '_')
                        
                        # 尝试插入字体
                        page.insert_font(fontname=fontname, fontfile=font_path)
                        logger.info(f"成功使用系统字体 '{font_filename}' 作为 '{fontname}'")
                        return fontname
                except Exception as e:
                    logger.debug(f"系统字体 '{os.path.basename(font_path)}' 插入失败: {e}")
        
        # 4. 无法找到任何适合的字体，抛出异常
        error_msg = f"无法找到适合目标语言 '{target_lang}' 的字体。请安装支持该语言的字体，例如Arial Unicode或其他支持{target_lang}语言的字体。"
        logger.error(error_msg)
        raise ValueError(error_msg)
    

    
    def _draw_translated_table(self, page, table, target_lang="zh"):
        """在页面上绘制翻译后的表格
        
        Args:
            page (fitz.Page): PDF页面对象
            table: PdfTable对象
            target_lang (str): 目标语言代码
        """
        # 使用cells属性
        table_cells = table.cells
        if not table_cells:
            logger.warning("表格数据为空，跳过绘制")
            return
        
        logger.info(f"开始绘制表格，共 {len(table_cells)} 行 {len(table_cells[0])} 列")
        
        # 获取表格边界框信息
        table_bbox = table.bbox
        logger.info(f"表格边界框: {table_bbox}")
        
        # 获取行高和列宽信息
        row_heights = table.row_heights
        col_widths = table.col_widths
        logger.info(f"行高: {row_heights}")
        logger.info(f"列宽: {col_widths}")
        
        # 获取适合目标语言的字体，使用与文本块相同的逻辑
        suitable_font = self._get_suitable_font(page, 'GoogleSansText-Regular', target_lang)
        logger.info(f"适合的字体: 目标语言='{target_lang}', 选择='{suitable_font}'")
        
        # 绘制表格边框和文本
        logger.info(f"开始绘制表格单元格，共 {len(table_cells)} 行 {len(table_cells[0])} 列")
        
        for i, row in enumerate(table_cells):
            for j, cell in enumerate(row):
                # 记录单元格位置信息
                is_corner_cell = (i == 0 and j == 0) or (i == 0 and j == len(row) - 1) or (i == len(table_cells) - 1 and j == 0) or (i == len(table_cells) - 1 and j == len(row) - 1)
                cell_position = "角落" if is_corner_cell else "中间"
                logger.info(f"处理{cell_position}单元格: 行={i+1}, 列={j+1}")
                
                # 检查cell类型
                logger.info(f"单元格类型: {type(cell)}, 内容: {cell}")
                
                if isinstance(cell, dict):
                    cell_text = cell.get('text', '')
                    cell_bbox = cell.get('bbox')
                    logger.info(f"单元格是字典，文本: '{cell_text}', 边界框: {cell_bbox}")
                elif hasattr(cell, 'text') and hasattr(cell, 'bbox'):
                    cell_text = cell.text
                    cell_bbox = cell.bbox
                    logger.info(f"单元格是对象，文本: '{cell_text}', 边界框: {cell_bbox}")
                else:
                    cell_text = str(cell)
                    cell_bbox = None
                    logger.info(f"单元格是其他类型，转换为文本: '{cell_text}', 无边界框")
                
                # 如果有单元格边界框信息，使用它
                if cell_bbox:
                    x0, y0, x1, y1 = cell_bbox
                    cell_width = x1 - x0
                    cell_height = y1 - y0
                    logger.info(f"使用单元格边界框: 位置=({x0:.2f}, {y0:.2f}), 大小=({cell_width:.2f}x{cell_height:.2f})")
                else:
                    # 没有边界框信息，使用表格边界框和行列信息计算
                    if table_bbox and row_heights and col_widths:
                        table_x0, table_y0, table_x1, table_y1 = table_bbox
                        
                        # 计算当前单元格的位置
                        current_x = table_x0
                        for k in range(j):
                            if k < len(col_widths):
                                current_x += col_widths[k]
                        
                        current_y = table_y0
                        for k in range(i):
                            if k < len(row_heights):
                                current_y += row_heights[k]
                        
                        # 计算单元格大小
                        cell_width = col_widths[j] if j < len(col_widths) else (table_x1 - table_x0) / len(row)
                        cell_height = row_heights[i] if i < len(row_heights) else (table_y1 - table_y0) / len(table_cells)
                        
                        x0 = current_x
                        y0 = current_y
                        x1 = current_x + cell_width
                        y1 = current_y + cell_height
                        logger.info(f"计算单元格位置: 位置=({x0:.2f}, {y0:.2f}), 大小=({cell_width:.2f}x{cell_height:.2f})")
                        logger.info(f"使用的行高: {row_heights[i] if i < len(row_heights) else '计算值'}")
                        logger.info(f"使用的列宽: {col_widths[j] if j < len(col_widths) else '计算值'}")
                    else:
                        # 使用默认位置和大小
                        x0 = 50 + j * 100
                        y0 = 200 + i * 30
                        x1 = 150 + j * 100
                        y1 = 230 + i * 30
                        cell_width = 100
                        cell_height = 30
                        logger.warning("没有足够的表格信息，使用默认位置和大小")
                
                rect = fitz.Rect(x0, y0, x1, y1)
                logger.info(f"单元格矩形: {rect}")
                
                # 绘制单元格边框
                try:
                    page.draw_rect(rect, color=(0, 0, 0), width=0.5)
                    logger.info(f"成功绘制单元格 ({i+1},{j+1}) 边框")
                except Exception as e:
                    logger.error(f"绘制单元格 ({i+1},{j+1}) 边框异常: {str(e)}")
                
                # 绘制单元格背景，无论是否有文本
                try:
                    page.draw_rect(rect, color=(1, 1, 1), fill=True, width=0)
                    logger.debug(f"成功绘制单元格 ({i+1},{j+1}) 背景")
                except Exception as e:
                    logger.error(f"绘制单元格 ({i+1},{j+1}) 背景异常: {str(e)}")
                
                # 绘制单元格文本
                if cell_text:
                    logger.info(f"开始绘制单元格 ({i+1},{j+1}) 文本: '{cell_text}'")
                    
                    # 动态计算字体大小
                    base_font_size = min(cell_height * 0.8, 12)  # 不超过单元格高度的80%，最大12
                    logger.info(f"计算字体大小: 基础大小={base_font_size:.2f}")
                    
                    # 尝试绘制文本，支持字体大小调整
                    max_attempts = 5
                    success = False
                    
                    for attempt in range(1, max_attempts + 1):
                        # 计算当前尝试的字体大小
                        if attempt == 1:
                            current_font_size = base_font_size
                        else:
                            current_font_size = base_font_size * (1 - (attempt - 1) * 0.1)
                            current_font_size = max(current_font_size, base_font_size * 0.5)  # 不小于原大小的50%
                        
                        logger.info(f"尝试 {attempt}/{max_attempts}: 字体大小={current_font_size:.2f}")
                        
                        try:
                            # 尝试绘制文本
                            result = page.insert_textbox(
                                rect,
                                cell_text,
                                fontname=suitable_font,
                                fontsize=current_font_size,
                                color=(0, 0, 0),
                                align=1  # 居中对齐
                            )
                            
                            logger.info(f"文本绘制结果: {result}, 字体: {suitable_font}")
                            
                            if result >= 0:
                                logger.info(f"单元格 ({i+1},{j+1}) 文本绘制成功，插入了 {result} 个字符，使用字体大小: {current_font_size:.2f}")
                                success = True
                                break
                            
                            # 文本溢出，需要调整
                            logger.info(f"单元格 ({i+1},{j+1}) 文本溢出，返回值: {result}，尝试调整字体大小")
                            
                        except Exception as e:
                            logger.error(f"单元格 ({i+1},{j+1}) 文本绘制异常: {str(e)}")
                    
                    if not success:
                        logger.warning(f"单元格 ({i+1},{j+1}) 文本绘制失败，使用最小字体大小")
                        # 使用最小字体大小尝试最后一次
                        try:
                            result = page.insert_textbox(
                                rect,
                                cell_text,
                                fontname=suitable_font,
                                fontsize=base_font_size * 0.5,
                                color=(0, 0, 0),
                                align=1  # 居中对齐
                            )
                            logger.info(f"单元格 ({i+1},{j+1}) 最后尝试绘制，返回值: {result}")
                        except Exception as e:
                            logger.error(f"单元格 ({i+1},{j+1}) 最后尝试绘制异常: {str(e)}")
                    
                    # 记录单元格绘制状态
                    if success:
                        logger.info(f"✅ 单元格 ({i+1},{j+1}) 绘制完成: '{cell_text[:30]}{'...' if len(cell_text) > 30 else ''}'")
                    else:
                        logger.warning(f"❌ 单元格 ({i+1},{j+1}) 绘制失败: '{cell_text[:30]}{'...' if len(cell_text) > 30 else ''}'")
                else:
                    logger.info(f"单元格 ({i+1},{j+1}) 无文本，但已绘制背景和边框")
                    # 即使没有文本，也确保绘制边框
                    try:
                        page.draw_rect(rect, color=(0, 0, 0), width=0.5)
                        logger.debug(f"成功绘制空单元格 ({i+1},{j+1}) 边框")
                    except Exception as e:
                        logger.error(f"绘制空单元格 ({i+1},{j+1}) 边框异常: {str(e)}")
        
        logger.info("表格绘制完成")
    
    def _get_system_fonts(self):
        """从系统中获取可用字体列表
        
        Returns:
            list: 系统可用字体完整路径列表
        """
        system_fonts = []
        try:
            # 获取系统字体目录
            if sys.platform == 'win32':
                # Windows系统字体目录
                font_dirs = [r'C:\Windows\Fonts']
            elif sys.platform == 'darwin':
                # macOS系统字体目录
                font_dirs = [
                    '/System/Library/Fonts',
                    '/Library/Fonts',
                    os.path.expanduser('~/Library/Fonts')
                ]
            else:
                # Linux系统字体目录
                font_dirs = [
                    '/usr/share/fonts',
                    '/usr/local/share/fonts',
                    os.path.expanduser('~/.fonts')
                ]
            
            # 遍历字体目录，获取字体文件
            for font_dir in font_dirs:
                if os.path.exists(font_dir):
                    for root, _, files in os.walk(font_dir):
                        for file in files:
                            if file.endswith(('.ttf', '.otf', '.ttc')):  # 考虑TrueType、OpenType和TrueType集合字体
                                # 获取字体完整路径
                                font_path = os.path.join(root, file)
                                system_fonts.append(font_path)
            
            # 去重并排序
            system_fonts = list(set(system_fonts))
            system_fonts.sort()  # 按字母顺序排序，提高可预测性
            logger.info(f"从系统获取到 {len(system_fonts)} 种可用字体")
        except Exception as e:
            logger.warning(f"获取系统字体列表失败: {e}")
            system_fonts = []
        
        return system_fonts

    def _check_font_support(self, font_path, target_lang):
        """检查字体是否真正支持目标语言

        Args:
            font_path (str): 字体文件路径
            target_lang (str): 目标语言代码
            
        Returns:
            bool: 字体是否真正支持目标语言
        """
        # 1. 对于非中文目标语言，简化检测
        if target_lang not in ['zh', 'ja', 'ko']:
            logger.debug(f"目标语言 '{target_lang}' 为非复杂语言，默认支持")
            return True
        
        try:
            # 2. 获取字体文件名
            font_filename = os.path.basename(font_path)
            
            # 3. 尝试加载字体
            font = ImageFont.truetype(font_path, 12)
            
            # 4. 获取目标语言的测试字符
            test_chars = {
                'zh': '你好世界',
                'en': 'Hello World',
                'ja': 'こんにちは世界',
                'ko': '안녕하세요 세계'
            }
            test_char = test_chars.get(target_lang, test_chars['en'])
            
            # 5. 检查字体是否包含测试字符的字形
            # 使用getbbox检查每个字符的宽度，替换字符宽度通常为0或固定值
            for char in test_char:
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
                # 如果字符宽度为0或非常小，说明字体不支持该字符
                if char_width < 1:
                    logger.debug(f"字体 '{font_filename}' 不包含字符 '{char}' 的字形")
                    return False
            
            logger.debug(f"字体 '{font_filename}' 支持目标语言 '{target_lang}'")
            return True
        except Exception as e:
            logger.debug(f"字体 '{os.path.basename(font_path)}' 加载失败或不支持目标语言 '{target_lang}': {e}")
            return False
