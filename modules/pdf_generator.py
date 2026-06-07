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
    
    def generate_pdf(self, original_pdf_path, translated_content, output_pdf_path, target_lang="zh", target_pages=None):
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
            logger.warning("PDF生成器未接收到blocks信息，无法绘制翻译文本")
        
        if not os.path.exists(original_pdf_path):
            logger.error(f"原始PDF文件不存在: {original_pdf_path}")
            raise FileNotFoundError(f"原始PDF文件不存在: {original_pdf_path}")
        
        try:
            # 打开原始PDF
            with fitz.open(original_pdf_path) as original_doc:
                logger.info(f"成功打开原始PDF，总页数: {len(original_doc)}")
                
                # 创建新的PDF文档
                new_doc = fitz.open()
                try:
                    logger.info("创建新的PDF文档成功")

                    # 记录翻译内容概览
                    logger.info(f"翻译内容: 完整文本块 {len(translated_content.get('blocks', []))}, 表格 {len(translated_content.get('tables', []))}")

                    # 处理原始PDF的所有页面（包括无翻译内容的页面）
                    total_original_pages = len(original_doc)
                    logger.info(f"原始PDF总页数: {total_original_pages}")
                    
                    # 确定要输出的页面范围
                    if target_pages:
                        pages_to_output = [p for p in target_pages if 1 <= p <= total_original_pages]
                        logger.info(f"指定输出页码: {pages_to_output}")
                    else:
                        pages_to_output = list(range(1, total_original_pages + 1))
                    
                    # 构建页码到翻译内容的映射，方便查找
                    blocks_by_page = {}
                    for blocks_content in translated_content.get('blocks', []):
                        blocks_by_page[blocks_content.page_num] = blocks_content

                    tables_by_page = {}
                    for table in translated_content.get('tables', []):
                        tables_by_page.setdefault(table.page_num, []).append(table)

                    for page_num in pages_to_output:
                        original_page_idx = page_num - 1
                        original_page = original_doc[original_page_idx]

                        # 克隆原始页面到新文档
                        new_page = new_doc.new_page(width=original_page.rect.width, height=original_page.rect.height)
                        new_page.show_pdf_page(new_page.rect, original_doc, original_page_idx)

                        # 获取当前页的翻译内容
                        page_translated_blocks = blocks_by_page.get(page_num)

                        if page_translated_blocks and page_translated_blocks.text_blocks:
                            blocks_count = len(page_translated_blocks.text_blocks)
                            logger.info(f"第 {page_num} 页有 {blocks_count} 个完整文本块")
                            self._draw_translated_text(new_page, page_translated_blocks, target_lang)
                            logger.info(f"第 {page_num} 页绘制完成")
                        else:
                            logger.info(f"第 {page_num} 页无翻译文本块，保留原始页面")

                        # 处理表格（如果有）
                        page_tables = tables_by_page.get(page_num, [])
                        if page_tables:
                            logger.info(f"第 {page_num} 页有 {len(page_tables)} 个表格需要处理")
                            for i, table in enumerate(page_tables):
                                self._draw_translated_table(new_page, table, target_lang)
                                logger.info(f"第 {page_num} 页表格 {i+1} 绘制完成")

                    # 保存新PDF
                    logger.info(f"开始保存新PDF: {output_pdf_path}")

                    # 在保存文档之前获取总页数
                    total_pages = len(new_doc)

                    # 保存文档
                    new_doc.save(output_pdf_path)
                finally:
                    new_doc.close()
                
                # 使用预存的总页数记录日志，避免在文档关闭后访问
                logger.info(f"PDF生成完成，输出文件: {output_pdf_path}, 总页数: {total_pages}")
                
        except Exception as e:
            logger.error(f"生成PDF时出错: {str(e)}", exc_info=True)
            raise Exception(f"生成PDF时出错: {str(e)}")
    
    def _render_formula_image(self, latex, fontsize=12):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import io
        fig, ax = plt.subplots(figsize=(0.01, 0.01))
        ax.axis('off')
        text = ax.text(0, 0, f'${latex}$', fontsize=fontsize, ha='left', va='bottom')
        fig.canvas.draw()
        bbox = text.get_window_extent()
        fig.set_size_inches(bbox.width / fig.dpi + 0.1, bbox.height / fig.dpi + 0.05)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0.02, transparent=True)
        plt.close(fig)
        buf.seek(0)
        return buf

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
                logger.info("颜色接近白色，自动改为黑色")
            
            # 获取适合目标语言的字体
            suitable_font = self._get_suitable_font(page, original_font, target_lang)
            logger.info(f"适合的字体: 原字体='{original_font}', 目标语言='{target_lang}', 选择='{suitable_font}'")
            
            # 创建文本框
            rect = fitz.Rect(block_bbox[0], block_bbox[1], block_bbox[2], block_bbox[3])
            logger.debug(f"文本框尺寸: {rect.width}x{rect.height}")

            bg_padding = max(3, min(original_font_size * 0.4, 8))
            bg_rect = fitz.Rect(
                max(rect.x0 - bg_padding, 0),
                max(rect.y0 - bg_padding, 0),
                min(rect.x1 + bg_padding, page.rect.width),
                min(rect.y1 + bg_padding, page.rect.height)
            )
            page.draw_rect(bg_rect, color=(1, 1, 1), fill=True, width=0)
            logger.debug(f"绘制背景色覆盖原文，区域: {bg_rect} (padding={bg_padding:.1f})")

            if getattr(full_block, 'is_formula', False) and full_block.block_text:
                try:
                    img_buf = self._render_formula_image(full_block.block_text, fontsize=original_font_size)
                    page.insert_image(rect, stream=img_buf.getvalue())
                    continue
                except Exception as e:
                    logger.warning(f'公式渲染失败，降级为文本: {e}')
            
            # 使用默认左对齐
            alignment = 0
            logger.info(f"使用对齐方式: {alignment} (0=左对齐, 1=居中, 2=右对齐)")
            
            # 不再使用字体回退列表，只使用适合的字体
            max_attempts = 5
            success = False
            current_rect = rect
            
            for attempt in range(1, max_attempts + 1):
                try:
                    # 计算当前尝试的调整策略
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
                        logger.info(f"[OK] 文本渲染成功，插入了 {result} 个字符，使用字体大小: {adjusted_font_size}，文本框大小: {current_rect}")
                        logger.debug(f"渲染文本内容: '{translated_text[:100]}...' (完整长度={len(translated_text)})")
                        success = True
                        break
                    
                    # 文本溢出，需要调整
                    logger.warning(f"[WARN] 文本溢出，返回值: {result}，当前字体大小: {adjusted_font_size}，文本框: {current_rect}")
                    logger.warning(f"溢出文本: '{translated_text[:100]}...' (完整长度={len(translated_text)})")
                    
                    # 调整文本框大小（仅前3次尝试）
                except Exception as e:
                    logger.warning(f"[FAIL] 绘制失败: {e}")
                    break
            
            if not success:
                min_font_size = original_font_size * 0.5
                for font_ratio in [0.6, 0.5]:
                    adjusted_font_size = original_font_size * font_ratio
                    try:
                        result = page.insert_textbox(
                            current_rect,
                            translated_text,
                            fontname=suitable_font,
                            fontsize=adjusted_font_size,
                            color=rgb_color,
                            align=alignment
                        )
                        if result >= 0:
                            logger.info(f"[OK] 缩小字体到{font_ratio*100:.0f}%后渲染成功，字体大小: {adjusted_font_size}")
                            success = True
                            break
                        logger.warning(f"缩小字体到{font_ratio*100:.0f}%仍溢出，继续尝试")
                    except Exception as e:
                        logger.warning(f"缩小字体到{font_ratio*100:.0f}%绘制失败: {e}")
                        break

            if not success:
                truncated_text = translated_text
                min_font_size = original_font_size * 0.5
                ellipsis = "..."
                max_truncation_attempts = 10
                for trunc_attempt in range(1, max_truncation_attempts + 1):
                    ratio = 1.0 - trunc_attempt * 0.1
                    if ratio <= 0.1:
                        break
                    truncated_text = translated_text[:max(1, int(len(translated_text) * ratio))]
                    if not truncated_text.endswith(ellipsis):
                        truncated_text = truncated_text.rstrip() + ellipsis
                    try:
                        result = page.insert_textbox(
                            current_rect,
                            truncated_text,
                            fontname=suitable_font,
                            fontsize=min_font_size,
                            color=rgb_color,
                            align=alignment
                        )
                        if result >= 0:
                            logger.warning(
                                f"截断文本后渲染成功: 原始长度={len(translated_text)}, "
                                f"截断后长度={len(truncated_text)}, 截断比例={ratio:.0%}, "
                                f"字体大小={min_font_size:.1f}"
                            )
                            success = True
                            break
                        logger.debug(f"截断到{ratio:.0%}仍溢出，继续截断")
                    except Exception as e:
                        logger.warning(f"截断文本绘制失败: {e}")
                        break

            if not success:
                logger.warning(f"所有尝试（含截断）均失败，跳过文本块绘制: '{translated_text[:50]}...'")
        
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
                logger.info(f"尝试使用原始字体 '{original_font}'")
                page.insert_font(fontname=original_font, fontfile=None)
                # 检查原始字体是否支持目标语言字符
                if self._check_embedded_font_support(page, original_font, target_lang):
                    logger.info(f"原始字体 '{original_font}' 支持目标语言 '{target_lang}'，直接使用")
                    return original_font
                else:
                    logger.info(f"原始字体 '{original_font}' 不支持目标语言 '{target_lang}'，跳过")
            except Exception as e:
                logger.warning(f"原始字体 '{original_font}' 插入失败: {e}")
        
        # 2. 从系统获取可用字体列表
        system_font_paths = self._get_system_fonts()
        logger.info(f"系统字体列表获取完成，共 {len(system_font_paths)} 种字体")
        
        # 3. 从系统字体中选择支持目标语言的字体
        if system_font_paths:
            logger.info(f"开始从系统字体中选择支持 '{target_lang}' 的字体")
            
            # 特殊处理Arial Unicode.ttf，它支持多种语言
            arial_unicode_found = False
            for font_path in system_font_paths:
                if 'Arial Unicode.ttf' in font_path:
                    arial_unicode_found = True
                    try:
                        logger.info(f"找到Arial Unicode字体: {font_path}")
                        # 使用自定义短名称插入字体
                        fontname = "arialuni"
                        page.insert_font(fontname=fontname, fontfile=font_path)
                        logger.info(f"成功使用Arial Unicode字体作为 '{fontname}'")
                        return fontname
                    except Exception as e:
                        logger.error(f"Arial Unicode字体插入失败: {e}")
                        continue
            
            if not arial_unicode_found:
                logger.info("未找到Arial Unicode字体，继续搜索其他字体")
            
            # 遍历所有系统字体路径
            compatible_fonts = []
            for font_path in system_font_paths:
                try:
                    # 检查字体是否支持目标语言
                    if self._check_font_support(font_path, target_lang):
                        compatible_fonts.append(font_path)
                        logger.debug(f"字体 '{os.path.basename(font_path)}' 支持目标语言 '{target_lang}'")
                except Exception as e:
                    logger.debug(f"检查字体 '{os.path.basename(font_path)}' 时出错: {e}")
            
            logger.info(f"找到 {len(compatible_fonts)} 种支持 '{target_lang}' 的字体")
            
            # 尝试使用找到的兼容字体
            for font_path in compatible_fonts:
                try:
                    logger.info(f"尝试使用兼容字体: {font_path}")
                    # 创建自定义短名称，去除空格和特殊字符
                    font_filename = os.path.basename(font_path)
                    fontname = os.path.splitext(font_filename)[0].replace(' ', '_')
                    fontname = ''.join(c for c in fontname if c.isalnum() or c == '_')
                    
                    # 尝试插入字体
                    page.insert_font(fontname=fontname, fontfile=font_path)
                    logger.info(f"成功使用系统字体 '{font_filename}' 作为 '{fontname}'")
                    return fontname
                except Exception as e:
                    logger.warning(f"系统字体 '{os.path.basename(font_path)}' 插入失败: {e}")
                    continue
        
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
        logger.info(f"[表格绘制] 接收到表格数据: 页码={table.page_num}, 表格索引={table.table_idx}, cells行数={len(table_cells) if table_cells else 0}")
        
        if not table_cells:
            logger.warning("[表格绘制] 表格数据为空，跳过绘制")
            return
        
        # 记录表格所有单元格的内容，用于诊断
        logger.info("[表格绘制] 表格所有单元格内容预览:")
        for row_idx, row in enumerate(table_cells):
            for col_idx, cell in enumerate(row):
                if cell and hasattr(cell, 'text') and cell.text:
                    text_preview = cell.text[:30] + '...' if len(cell.text) > 30 else cell.text
                    logger.info(f"[表格绘制] 单元格 ({row_idx},{col_idx}): '{text_preview}'")
        
        logger.info(f"[表格绘制] 开始绘制表格，共 {len(table_cells)} 行 {len(table_cells[0])} 列")
        
        # 获取表格边界框信息
        table_bbox = table.bbox
        logger.warning(f"[TABLE_DIAG] 表格边界框: {table_bbox}, 类型: {type(table_bbox)}")
        
        # 获取行高和列宽信息
        row_heights = table.row_heights
        col_widths = table.col_widths
        logger.info(f"行高: {row_heights}")
        logger.info(f"列宽: {col_widths}")

        if table_bbox:
            table_x0, table_y0, table_x1, table_y1 = table_bbox
        
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
                    logger.info(f"[表格绘制] 单元格 ({i},{j}) 是字典，文本: '{cell_text}', 边界框: {cell_bbox}")
                elif hasattr(cell, 'text') and hasattr(cell, 'bbox'):
                    cell_text = cell.text
                    cell_bbox = cell.bbox
                    text_preview = cell_text[:50] + '...' if len(cell_text) > 50 else cell_text
                    logger.info(f"[表格绘制] 单元格 ({i},{j}) 是对象，文本: '{text_preview}', 边界框: {cell_bbox}")
                    # 增加关键日志：判断是否为原文
                    if cell_text and len(cell_text) > 0:
                        # 简单判断：如果包含英文字母且没有中文字符，可能是原文
                        has_english = any(c.isalpha() and ord(c) < 128 for c in cell_text)
                        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in cell_text)
                        if has_english and not has_chinese and target_lang == 'zh':
                            logger.warning(f"[表格绘制] [WARN] 单元格 ({i},{j}) 可能包含原文(英文)而非译文: '{text_preview}'")
                        elif has_chinese and target_lang == 'zh':
                            logger.info(f"[表格绘制] [OK] 单元格 ({i},{j}) 包含中文译文: '{text_preview}'")
                else:
                    cell_text = str(cell)
                    cell_bbox = None
                    logger.info(f"[表格绘制] 单元格 ({i},{j}) 是其他类型，转换为文本: '{cell_text}', 无边界框")
                
                # 如果有单元格边界框信息，使用它（跳过零大小bbox）
                if cell_bbox and not (cell_bbox[0] == 0 and cell_bbox[1] == 0 and cell_bbox[2] == 0 and cell_bbox[3] == 0):
                    x0, y0, x1, y1 = cell_bbox
                    cell_width = x1 - x0
                    cell_height = y1 - y0
                    if cell_width > 0 and cell_height > 0:
                        logger.info(f"使用单元格边界框: 位置=({x0:.2f}, {y0:.2f}), 大小=({cell_width:.2f}x{cell_height:.2f})")
                    else:
                        logger.info("单元格边界框大小为零，使用计算位置")
                        cell_bbox = None
                else:
                    # 没有边界框信息，使用表格边界框和行列信息计算
                    if table_bbox and row_heights and col_widths:
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
                        num_rows = len(table_cells)
                        num_cols = len(table_cells[0]) if num_rows > 0 else 1
                        cell_width = (table_x1 - table_x0) / num_cols if num_cols > 0 else 100
                        cell_height = (table_y1 - table_y0) / num_rows if num_rows > 0 else 30
                        x0 = table_x0 + j * cell_width
                        y0 = table_y0 + i * cell_height
                        x1 = x0 + cell_width
                        y1 = y0 + cell_height
                
                rect = fitz.Rect(x0, y0, x1, y1)
                logger.info(f"单元格矩形: {rect}")

                # 绘制单元格背景，无论是否有文本
                try:
                    cell_bg_rect = fitz.Rect(
                        max(rect.x0 - 2, 0),
                        rect.y0,
                        min(rect.x1 + 2, page.rect.width),
                        rect.y1
                    )
                    page.draw_rect(cell_bg_rect, color=(1, 1, 1), fill=True, width=0)
                    logger.debug(f"成功绘制单元格 ({i+1},{j+1}) 背景, 区域: {cell_bg_rect}")
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
                        logger.info(f"[OK] 单元格 ({i+1},{j+1}) 绘制完成: '{cell_text[:30]}{'...' if len(cell_text) > 30 else ''}'")
                    else:
                        logger.warning(f"[FAIL] 单元格 ({i+1},{j+1}) 绘制失败: '{cell_text[:30]}{'...' if len(cell_text) > 30 else ''}'")
                else:
                    logger.info(f"单元格 ({i+1},{j+1}) 无文本，但已绘制背景")
        
        # 统一绘制表格网格线（外框 + 内部线条）
        try:
            if table_bbox:
                table_rect = fitz.Rect(table_x0, table_y0, table_x1, table_y1)
                # 外框
                page.draw_rect(table_rect, color=(0, 0, 0), width=1)
                # 内部水平线（每行的底部边界）
                for row_i in range(len(row_heights) - 1):
                    line_y = table_y0 + sum(row_heights[:row_i + 1])
                    page.draw_line(
                        fitz.Point(table_x0, line_y),
                        fitz.Point(table_x1, line_y),
                        color=(0, 0, 0), width=0.5
                    )
                # 内部垂直线（每列的右侧边界）
                for col_j in range(len(col_widths) - 1):
                    line_x = table_x0 + sum(col_widths[:col_j + 1])
                    page.draw_line(
                        fitz.Point(line_x, table_y0),
                        fitz.Point(line_x, table_y1),
                        color=(0, 0, 0), width=0.5
                    )
                logger.info("表格网格线绘制完成")
        except Exception as e:
            logger.error(f"绘制表格网格线异常: {e}")
        
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

    def _check_embedded_font_support(self, page, fontname, target_lang):
        """检查PDF内嵌字体是否支持目标语言字符

        通过在临时页面上用该字体插入测试文本来检测。
        如果字体不支持目标语言字符，PyMuPDF会使用替换字形，
        导致插入的文本长度与预期不符。

        Args:
            page (fitz.Page): PDF页面对象
            fontname (str): 字体名称
            target_lang (str): 目标语言代码

        Returns:
            bool: 字体是否支持目标语言字符
        """
        # 获取目标语言的测试字符
        test_chars = {
            'zh': '你好',
            'en': 'Hello',
            'de': 'äöüß',
            'fr': 'éèêàç',
            'es': 'ñ¿¡',
            'pt': 'ãç',
            'it': 'àèì',
            'nl': 'ëï',
            'ja': 'こんにちは',
            'ko': '안녕',
            'th': 'สวัสดี',
            'vi': 'chào',
            'ru': 'Привет',
            'ar': 'مرحبا',
            'hi': 'नमस्ते',
            'he': 'שלום',
        }
        test_char = test_chars.get(target_lang, test_chars['en'])

        # 拉丁语言（en/fr/de/es/pt/it/nl）的内嵌字体通常支持拉丁字符
        latin_langs = {'en', 'fr', 'de', 'es', 'pt', 'it', 'nl'}
        if target_lang in latin_langs:
            # 尝试从系统字体中查找该字体文件进行精确检测
            system_font_paths = self._get_system_fonts()
            for font_path in system_font_paths:
                font_filename = os.path.basename(font_path)
                if fontname.lower().replace('-', '').replace(' ', '') in font_filename.lower().replace('-', '').replace(' ', ''):
                    return self._check_font_support(font_path, target_lang)
            # 找不到字体文件，拉丁语言默认支持
            logger.debug(f"拉丁语言 '{target_lang}'，内嵌字体 '{fontname}' 默认支持")
            return True

        # 非拉丁语言：尝试从系统字体中查找该字体文件进行检测
        system_font_paths = self._get_system_fonts()
        for font_path in system_font_paths:
            font_filename = os.path.basename(font_path)
            if fontname.lower().replace('-', '').replace(' ', '') in font_filename.lower().replace('-', '').replace(' ', ''):
                result = self._check_font_support(font_path, target_lang)
                logger.debug(f"内嵌字体 '{fontname}' 系统文件检测: {result}")
                return result

        # 无法找到字体文件，非拉丁语言默认不支持
        logger.debug(f"内嵌字体 '{fontname}' 未找到系统文件，非拉丁语言 '{target_lang}' 默认不支持")
        return False

    def _check_font_support(self, font_path, target_lang):
        """检查字体是否真正支持目标语言

        Args:
            font_path (str): 字体文件路径
            target_lang (str): 目标语言代码
            
        Returns:
            bool: 字体是否真正支持目标语言
        """
        try:
            # 获取字体文件名
            font_filename = os.path.basename(font_path)
            
            # 尝试加载字体
            font = ImageFont.truetype(font_path, 12)
            
            # 获取目标语言的测试字符
            test_chars = {
                'zh': '你好世界',
                'en': 'Hello World',
                'de': 'äöüßÄÖÜ',
                'fr': 'éèêàçîôù',
                'es': 'ñ¿¡áéíóú',
                'pt': 'ãçáéíóú',
                'it': 'àèìòù',
                'nl': 'ëï',
                'ja': 'こんにちは世界',
                'ko': '안녕하세요 세계',
                'th': 'สวัสดี',
                'vi': 'Xin chào',
                'ru': 'Привет',
                'ar': 'مرحبا',
                'hi': 'नमस्ते',
                'he': 'שלום',
            }
            test_char = test_chars.get(target_lang, test_chars['en'])
            
            # 检查字体是否包含测试字符的字形
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
