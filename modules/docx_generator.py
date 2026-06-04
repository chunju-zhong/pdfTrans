import os
import re
import logging
from lxml import etree
from docx import Document
from models.merged_block import MergedBlock
from docx.shared import Inches, RGBColor, Pt

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
                    - bbox (tuple): 文本块边界框 (x0, y0, x1, y1) - 新增
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
            
            # 按页码组织合并后的翻译结果
            merged_by_page = {}
            for item in translated_content.get('merged_translations', []):
                page_num = item.page_num
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
            
            # 按页码组织表格
            tables_by_page = {}
            if 'tables' in translated_content:
                for table in translated_content['tables']:
                    page_num = table.page_num  # 使用page_num属性
                    if page_num not in tables_by_page:
                        tables_by_page[page_num] = []
                    tables_by_page[page_num].append(table)
            
            # 按页码组织原始文本块
            original_blocks_by_page = {}
            if 'blocks' in translated_content:
                for page in translated_content['blocks']:
                    page_num = page.page_num
                    if page_num not in original_blocks_by_page:
                        original_blocks_by_page[page_num] = []
                    # 原始文本块已经按垂直位置排序
                    original_blocks_by_page[page_num] = page.text_blocks
            
            # 获取所有页码的列表
            all_pages = set(merged_by_page.keys())
            all_pages.update(images_by_page.keys())
            all_pages.update(tables_by_page.keys())
            sorted_pages = sorted(all_pages)
            
            # 处理每页内容
            for i, page_num in enumerate(sorted_pages):
                logger.info(f"处理第 {page_num} 页")
                
                # 收集当前页的所有元素
                page_elements = []
                
                # 添加文本块元素
                text_blocks = merged_by_page.get(page_num, [])
                for block_idx, block in enumerate(text_blocks):
                    logger.info(f"处理第 {page_num} 页 文本块 {block_idx+1}: 内容='{block.block_text[:50]}...'")
                    
                    page_elements.append({
                        'type': 'text',
                        'content': block,
                        'block_idx': block_idx
                    })
                
                # 添加图像元素
                page_images = images_by_page.get(page_num, [])
                for image_idx, image in enumerate(page_images):
                    logger.info(f"处理第 {page_num} 页 图像 {image_idx+1}: 路径={image.image_path}")
                    
                    page_elements.append({
                        'type': 'image',
                        'content': image
                    })
                
                # 添加表格元素
                page_tables = tables_by_page.get(page_num, [])
                for table_idx, table in enumerate(page_tables):
                    logger.info(f"处理第 {page_num} 页 表格 {table_idx+1}")
                    
                    page_elements.append({
                        'type': 'table',
                        'content': table
                    })
                
                # 记录元素列表
                logger.info(f"第 {page_num} 页元素列表:")
                for i, elem in enumerate(page_elements):
                    elem_type = elem['type']
                    if elem_type == 'text':
                        content = elem['content'].block_text[:30] + '...'
                    elif elem_type == 'image':
                        content = f"图像: {elem['content'].image_path}"
                    else:
                        content = f"{elem_type}: {elem['content']}"
                    logger.info(f"  元素 {i+1}: 类型={elem_type}, 内容='{content}'")
                
                # 处理元素
                self._process_page_elements(doc, page_elements, original_blocks_by_page, page_num)
                
                # 只在不是最后一页时添加分页符
                if i < len(sorted_pages) - 1:
                    # 添加分页符
                    doc.add_page_break()
            
            # 保存文档
            output_dir = os.path.dirname(output_docx_path)
            os.makedirs(output_dir, exist_ok=True)
            
            doc.save(output_docx_path)
            logger.info(f"Word文档生成完成，输出文件: {output_docx_path}")
            
        except Exception as e:
            logger.error(f"生成Word文档时出错: {str(e)}", exc_info=True)
            raise Exception(f"生成Word文档时出错: {str(e)}")
    
    def _find_chart_position(self, image, original_blocks):
        """查找图表在原始文本块中的位置
        
        Args:
            image: 图像对象
            original_blocks: 原始文本块列表（已排序）
            
        Returns:
            tuple: (before_block, after_block) - 图表前后的原始块
        """
        chart_y = image.bbox[1]
        
        # 在已排序的原始文本块中查找图表前后的块
        # 由于原始文本块已经按垂直位置排序，可以使用线性查找
        before_block = None
        after_block = None
        
        for i, block in enumerate(original_blocks):
            block_y = block.block_bbox[1]
            if block_y <= chart_y:
                before_block = block
            else:
                after_block = block
                break
        
        logger.info(f"图表位置查找完成: before_block={before_block.block_no if before_block else None}, after_block={after_block.block_no if after_block else None}")
        return before_block, after_block
    
    def _find_merged_block(self, before_block, after_block, merged_blocks, chart_y=None):
        """查找包含图表前后原始块的合并块
        
        Args:
            before_block: 图表前的原始块
            after_block: 图表后的原始块
            merged_blocks: 合并块列表
            chart_y: 图表的y坐标（可选），用于计算在合并块内的插入点
            
        Returns:
            tuple: (merged_block, position, is_within_merged_block, insertion_ratio)
                - merged_block: 包含图表的合并块
                - position: 位置关系 ('before', 'after', 'within')
                - is_within_merged_block: 图表是否位于合并块内部
                - insertion_ratio: 图表在合并块中的相对位置比例（0-1）
        """
        for block in merged_blocks:
            original_blocks = block.original_blocks
            original_block_nos = [b.block_no for b in original_blocks]
            
            # 检查before_block和after_block是否都在同一个合并块中
            before_in_block = before_block and before_block.block_no in original_block_nos
            after_in_block = after_block and after_block.block_no in original_block_nos
            
            if before_in_block and after_in_block:
                # 图表位于合并块内部
                logger.info(f"图表位于合并块内部: {block.block_text[:30]}...")
                
                if chart_y is not None:
                    # 计算插入点比例
                    merged_start_y = min(b.block_bbox[1] for b in original_blocks)
                    merged_end_y = max(b.block_bbox[3] for b in original_blocks)
                    merged_height = merged_end_y - merged_start_y
                    
                    if merged_height > 0:
                        insertion_ratio = (chart_y - merged_start_y) / merged_height
                        insertion_ratio = max(0.1, min(0.9, insertion_ratio))  # 限制在10%-90%之间
                        logger.info(f"计算合并块内插入点比例: {insertion_ratio:.2f}, 合并块范围: y0={merged_start_y}, y1={merged_end_y}")
                        return block, 'within', True, insertion_ratio
                
                return block, 'within', True, 0.5  # 默认中间位置
            
            # 检查before_block是否在当前合并块中（使用块编号）
            if before_block and before_block.block_no in original_block_nos:
                logger.info(f"找到包含before_block的合并块: {block.block_text[:30]}...")
                return block, 'after', False, None  # 图表在before_block之后
            
            # 检查after_block是否在当前合并块中（使用块编号）
            if after_block and after_block.block_no in original_block_nos:
                logger.info(f"找到包含after_block的合并块: {block.block_text[:30]}...")
                return block, 'before', False, None  # 图表在after_block之前
        
        logger.info("未找到包含图表前后原始块的合并块")
        return None, None, False, None
    
    def _process_page_elements(self, doc, page_elements, original_blocks_by_page, page_num):
        """处理页面元素，按顺序添加到Word文档
        
        Args:
            doc: Word文档对象
            page_elements (list): 页面元素列表
            original_blocks_by_page: 按页码组织的原始文本块
            page_num: 当前页码
        """
        logger.info(f"开始处理页面元素，元素数量: {len(page_elements)}")
        
        # 跟踪已处理的文本块索引
        processed_blocks = set()
        
        # 获取当前页面的原始文本块（已排序）
        original_blocks = original_blocks_by_page.get(page_num, [])
        
        # 分离文本块和图表元素
        text_elements = []
        chart_elements = []
        
        for element in page_elements:
            if element['type'] == 'text':
                text_elements.append(element)
            else:
                chart_elements.append(element)
        
        # 处理图表元素，确定它们的插入位置
        chart_insertions = []
        for chart in chart_elements:
            if chart['type'] == 'image' or chart['type'] == 'table':
                # 查找图表/表格在原始文本块中的位置
                before_block, after_block = None, None
                chart_y = None
                if hasattr(chart['content'], 'bbox'):
                    chart_y = chart['content'].bbox[1]
                    # 如果有bbox属性，使用与图像相同的位置查找逻辑
                    before_block, after_block = self._find_chart_position(chart['content'], original_blocks)
                
                # 查找包含图表/表格前后原始块的合并块
                merged_blocks = [e['content'] for e in text_elements]
                merged_block, position, is_within, insertion_ratio = self._find_merged_block(before_block, after_block, merged_blocks, chart_y)
                
                if merged_block:
                    chart_insertions.append((merged_block, position, chart, insertion_ratio))
                else:
                    # 如果没有找到合适的合并块，直接添加图表/表格
                    chart_insertions.append((None, 'end', chart, None))
        
        # 处理文本块和图表
        for element in text_elements:
            block = element['content']
            block_idx = element['block_idx']
            
            if block_idx not in processed_blocks:
                # 检查是否有图表需要插入到当前块之前
                for merged_block, position, chart, insertion_ratio in chart_insertions:
                    if merged_block == block and position == 'before':
                        # 插入图表到当前块之前
                        if chart['type'] == 'image':
                            logger.info(f"  在文本块之前插入图像: {chart['content'].image_path}")
                            self._add_image(doc, chart['content'])
                        elif chart['type'] == 'table':
                            logger.info("  在文本块之前插入表格")
                            self._add_table(doc, chart['content'])
                
                # 检查是否有图表需要插入到当前块内部
                for merged_block, position, chart, insertion_ratio in chart_insertions:
                    if merged_block == block and position == 'within':
                        # 在合并块内部插入图表，拆分文本
                        ratio_str = f"{insertion_ratio:.2f}" if insertion_ratio is not None else "0.5"
                        logger.info(f"  在合并块内部插入图表，插入点比例: {ratio_str}")
                        self._insert_element_in_text_block(doc, block, chart, insertion_ratio)
                        processed_blocks.add(block_idx)
                        logger.info(f"  合并块内部插入完成")
                        break
                
                # 如果没有在块内部插入，则正常添加文本块
                if block_idx not in processed_blocks:
                    # 添加文本块
                    logger.info(f"  添加文本块 {block_idx+1}: 内容='{block.block_text[:30]}...'")
                    self._add_merged_text(doc, block)
                    processed_blocks.add(block_idx)
                    logger.info(f"  文本块 {block_idx+1} 处理完成")
                    
                    # 检查是否有图表需要插入到当前块之后
                    for merged_block, position, chart, insertion_ratio in chart_insertions:
                        if merged_block == block and position == 'after':
                            # 插入图表到当前块之后
                            if chart['type'] == 'image':
                                logger.info(f"  在文本块之后插入图像: {chart['content'].image_path}")
                                self._add_image(doc, chart['content'])
                            elif chart['type'] == 'table':
                                logger.info("  在文本块之后插入表格")
                                self._add_table(doc, chart['content'])
        
        # 处理需要添加到文档末尾的图表
        for merged_block, position, chart, insertion_ratio in chart_insertions:
            if position == 'end':
                if chart['type'] == 'image':
                    logger.info(f"  在文档末尾插入图像: {chart['content'].image_path}")
                    self._add_image(doc, chart['content'])
                elif chart['type'] == 'table':
                    logger.info(f"  在文档末尾插入表格")
                    self._add_table(doc, chart['content'])
        
        logger.info(f"页面元素处理完成，已处理 {len(processed_blocks)} 个文本块")
    
    def _insert_element_in_text_block(self, doc, text_block, element, insertion_point):
        """在文本块内部插入元素，拆分文本
        
        Args:
            doc: Word文档对象
            text_block: 文本块对象
            element: 要插入的元素
            insertion_point: 插入点比例（0-1）
        """
        logger.info(f"拆分合并块，插入点: {insertion_point:.2f}, 合并块内容: '{text_block.block_text[:50]}...'")
        
        text = text_block.block_text
        text_length = len(text)
        
        # 计算插入位置
        split_index = int(text_length * insertion_point)
        
        # 尝试在单词边界拆分
        if split_index > 0 and split_index < text_length:
            # 向前查找空格或标点
            while split_index > 0 and text[split_index-1].isalnum():
                split_index -= 1
        
        # 拆分为前后两段
        text_before = text[:split_index].rstrip()
        text_after = text[split_index:].lstrip()
        
        logger.info(f"拆分结果: 前半部分='{text_before[:30]}...', 后半部分='{text_after[:30]}...'")
        
        # 添加前段文本
        if text_before:
            before_block = MergedBlock(
                block_text=text_before,
                original_blocks=text_block.original_blocks,
                max_width=text_block.max_width,
                max_height=text_block.max_height
            )
            self._add_merged_text(doc, before_block)
            logger.info("添加前段文本完成")
        
        # 添加元素
        if element['type'] == 'image':
            self._add_image(doc, element['content'])
            logger.info("添加图像完成")
        elif element['type'] == 'table':
            self._add_table(doc, element['content'])
            logger.info("添加表格完成")
        
        # 添加后段文本
        if text_after:
            after_block = MergedBlock(
                block_text=text_after,
                original_blocks=text_block.original_blocks,
                max_width=text_block.max_width,
                max_height=text_block.max_height
            )
            self._add_merged_text(doc, after_block)
            logger.info("添加后段文本完成")
    
    def _insert_formula_omml(self, paragraph, latex):
        try:
            from latex2mathml.converter import convert as latex_to_mathml

            # 预处理：剥离数学字体命令，避免生成 Unicode SMP 字符或 mathvariant 属性
            # latex2mathml 会将 \mathsf{F} 转为 Unicode Mathematical Alphanumeric 字符
            # (U+1D5A5)，这些字符在没有正确字体映射的 Word 环境中可能不可见。
            prev = None
            while prev != latex:
                prev = latex
                latex = re.sub(r'\\(?:mathsf|mathrm|mathbf|mathit|mathcal|mathbb|mathfrak|mathscr|mathtt)\{([^}]*)\}', r'\1', latex)

            mathml = latex_to_mathml(latex)
            mathml_tree = etree.fromstring(mathml.encode('utf-8'))
            omml_elem = self._mathml_to_omml_element(mathml_tree)
            if omml_elem is None:
                return False
            oMathPara = etree.SubElement(etree.Element('dummy'), '{http://schemas.openxmlformats.org/officeDocument/2006/math}oMathPara')
            oMath = etree.SubElement(oMathPara, '{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath')
            for child in omml_elem:
                oMath.append(child)
            paragraph._element.append(oMathPara)
            return True
        except Exception as e:
            logging.getLogger(__name__).warning(f'公式OMML转换失败，降级为文本: {e}')
            return False

    M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

    def _omml_tag(self, local):
        return f'{{{self.M_NS}}}{local}'

    def _make_mr(self, text, normal_text=False):
        r_elem = etree.Element(self._omml_tag('r'))
        if normal_text:
            rPr = etree.SubElement(r_elem, self._omml_tag('rPr'))
            nor_elem = etree.SubElement(rPr, self._omml_tag('nor'))
            nor_elem.set(f'{{{self.M_NS}}}val', '1')
        t_elem = etree.SubElement(r_elem, self._omml_tag('t'))
        t_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        t_elem.text = text
        return r_elem

    def _mathml_to_omml_element(self, mathml_elem, in_script_base=False):
        tag = etree.QName(mathml_elem.tag).localname if '}' in mathml_elem.tag else mathml_elem.tag
        children = list(mathml_elem)

        if tag == 'math':
            container = etree.Element(self._omml_tag('oMath'))
            for child in children:
                converted = self._mathml_to_omml_element(child)
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            container.append(item)
                    else:
                        container.append(converted)
            return container

        if tag in ('mrow', 'mstyle'):
            results = []
            for child in children:
                converted = self._mathml_to_omml_element(child)
                if converted is not None:
                    if isinstance(converted, list):
                        results.extend(converted)
                    else:
                        results.append(converted)
            return results if len(results) != 1 else results[0] if results else None

        if tag in ('mi', 'mo'):
            text = mathml_elem.text or ''
            return self._make_mr(text)

        if tag == 'mn':
            # 数字使用 normal text 渲染，避免 Word 中 Cambria Math 字体
            # 在 <m:sSup> 等结构中底数小数数字可能因字体回退而不可见
            # 仅在脚本基座（sSup/sSub/sSubSup 的 <m:e>）中启用 normal_text，
            # 避免顶层独立数字因 CJK Normal 字体（如 DengXian）在公式上下文中不可见
            text = mathml_elem.text or ''
            return self._make_mr(text, normal_text=in_script_base)

        if tag == 'mtext':
            text = mathml_elem.text or ''
            return self._make_mr(text)

        if tag == 'mfrac':
            f_elem = etree.Element(self._omml_tag('f'))
            fPr = etree.SubElement(f_elem, self._omml_tag('fPr'))
            etree.SubElement(fPr, self._omml_tag('ctrlPr'))
            num_elem = etree.SubElement(f_elem, self._omml_tag('num'))
            den_elem = etree.SubElement(f_elem, self._omml_tag('den'))
            if len(children) >= 1:
                converted = self._mathml_to_omml_element(children[0])
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            num_elem.append(item)
                    else:
                        num_elem.append(converted)
            if len(children) >= 2:
                converted = self._mathml_to_omml_element(children[1])
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            den_elem.append(item)
                    else:
                        den_elem.append(converted)
            return f_elem

        if tag == 'msup':
            sSup = etree.Element(self._omml_tag('sSup'))
            e_elem = etree.SubElement(sSup, self._omml_tag('e'))
            sup_elem = etree.SubElement(sSup, self._omml_tag('sup'))
            if len(children) >= 1:
                converted = self._mathml_to_omml_element(children[0], in_script_base=True)
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            e_elem.append(item)
                    else:
                        e_elem.append(converted)
            if len(children) >= 2:
                converted = self._mathml_to_omml_element(children[1])
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            sup_elem.append(item)
                    else:
                        sup_elem.append(converted)
            return sSup

        if tag == 'msub':
            sSub = etree.Element(self._omml_tag('sSub'))
            e_elem = etree.SubElement(sSub, self._omml_tag('e'))
            sub_elem = etree.SubElement(sSub, self._omml_tag('sub'))
            if len(children) >= 1:
                converted = self._mathml_to_omml_element(children[0], in_script_base=True)
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            e_elem.append(item)
                    else:
                        e_elem.append(converted)
            if len(children) >= 2:
                converted = self._mathml_to_omml_element(children[1])
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            sub_elem.append(item)
                    else:
                        sub_elem.append(converted)
            return sSub

        if tag == 'msubsup':
            sSubSup = etree.Element(self._omml_tag('sSubSup'))
            e_elem = etree.SubElement(sSubSup, self._omml_tag('e'))
            sub_elem = etree.SubElement(sSubSup, self._omml_tag('sub'))
            sup_elem = etree.SubElement(sSubSup, self._omml_tag('sup'))
            if len(children) >= 1:
                converted = self._mathml_to_omml_element(children[0], in_script_base=True)
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            e_elem.append(item)
                    else:
                        e_elem.append(converted)
            if len(children) >= 2:
                converted = self._mathml_to_omml_element(children[1])
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            sub_elem.append(item)
                    else:
                        sub_elem.append(converted)
            if len(children) >= 3:
                converted = self._mathml_to_omml_element(children[2])
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            sup_elem.append(item)
                    else:
                        sup_elem.append(converted)
            return sSubSup

        if tag == 'msqrt':
            rad = etree.Element(self._omml_tag('rad'))
            radPr = etree.SubElement(rad, self._omml_tag('radPr'))
            degHide = etree.SubElement(radPr, self._omml_tag('degHide'))
            degHide.set('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', '1')
            etree.SubElement(rad, self._omml_tag('deg'))
            e_elem = etree.SubElement(rad, self._omml_tag('e'))
            for child in children:
                converted = self._mathml_to_omml_element(child)
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            e_elem.append(item)
                    else:
                        e_elem.append(converted)
            return rad

        if tag == 'mover':
            acc = etree.Element(self._omml_tag('acc'))
            etree.SubElement(acc, self._omml_tag('accPr'))
            e_elem = etree.SubElement(acc, self._omml_tag('e'))
            if len(children) >= 1:
                converted = self._mathml_to_omml_element(children[0])
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            e_elem.append(item)
                    else:
                        e_elem.append(converted)
            return acc

        if tag == 'munder':
            groupChr = etree.Element(self._omml_tag('groupChr'))
            etree.SubElement(groupChr, self._omml_tag('groupChrPr'))
            e_elem = etree.SubElement(groupChr, self._omml_tag('e'))
            if len(children) >= 1:
                converted = self._mathml_to_omml_element(children[0])
                if converted is not None:
                    if isinstance(converted, list):
                        for item in converted:
                            e_elem.append(item)
                    else:
                        e_elem.append(converted)
            return groupChr

        results = []
        for child in children:
            converted = self._mathml_to_omml_element(child)
            if converted is not None:
                if isinstance(converted, list):
                    results.extend(converted)
                else:
                    results.append(converted)
        if not results:
            text = mathml_elem.text or ''
            if text.strip():
                return self._make_mr(text)
            return None
        return results if len(results) != 1 else results[0]

    @staticmethod
    def _extract_rgb(color):
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return r, g, b

    def _set_run_color(self, run, color):
        r, g, b = self._extract_rgb(color)
        run.font.color.rgb = RGBColor(r, g, b)

    def _add_merged_text(self, doc, translated_item):
        """添加翻译后的文本到Word文档
        
        Args:
            doc: Word文档对象
            translated_item: 翻译结果项（MergedBlock对象）
                - block_text (str): 翻译后的文本
                - font (str): 字体名称
                - font_size (float): 字体大小
                - color (int): 颜色值
                - bold (bool): 是否粗体
                - italic (bool): 是否斜体
        """
        paragraph = doc.add_paragraph()

        if hasattr(translated_item, 'original_blocks') and translated_item.original_blocks:
            # 先处理 formula 块（需要按块插入 OMML）
            for text_block in translated_item.original_blocks:
                if getattr(text_block, 'is_formula', False) and text_block.block_text:
                    self._insert_formula_omml(paragraph, text_block.block_text)

            # 有翻译文本时只写入一次，避免重复
            if hasattr(translated_item, 'block_text') and translated_item.block_text:
                text_to_write = translated_item.block_text
            elif translated_item.original_blocks:
                text_to_write = translated_item.original_blocks[0].block_text
            else:
                text_to_write = ''

            # 移除公式文本，避免在普通文本中重复输出公式 LaTeX
            for text_block in translated_item.original_blocks:
                if getattr(text_block, 'is_formula', False) and text_block.block_text:
                    if text_block.block_text in text_to_write:
                        text_to_write = text_to_write.replace(text_block.block_text, '')
            # 清理多余空白
            text_to_write = re.sub(r'  +', ' ', text_to_write).strip()

            if text_to_write.strip():
                cleaned_text = self._clean_xml_compatible_text(text_to_write)
                run = paragraph.add_run(cleaned_text)
                try:
                    # 使用第一个原始块的样式
                    first_block = translated_item.original_blocks[0]
                    run.font.name = first_block.font
                    run.font.size = Pt(first_block.font_size)
                    self._set_run_color(run, first_block.color)
                    run.bold = first_block.bold
                    run.italic = first_block.italic
                except Exception as e:
                    logger.warning(f"设置文本块样式失败: {e}")
        else:
            cleaned_text = self._clean_xml_compatible_text(translated_item.block_text)
            run = paragraph.add_run(cleaned_text)
            try:
                run.font.name = translated_item.font
                font_size = translated_item.font_size
                run.font.size = Pt(font_size)
                logger.info(f"应用字体大小: {font_size} 到文本: '{cleaned_text[:50]}...'")
                self._set_run_color(run, translated_item.color)
                run.bold = translated_item.bold
                run.italic = translated_item.italic
                logger.debug(f"添加翻译文本，内容: '{cleaned_text[:50]}...'，字体: {translated_item.font}，大小: {font_size}")
            except Exception as e:
                logger.warning(f"设置翻译文本样式失败: {e}")
    
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
            self._set_run_color(run, text_block.color)
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
            table: PdfTable对象
        """
        # 使用cells属性
        table_data = table.cells
        
        if not table_data:
            logger.warning("表格数据为空，跳过")
            return
        
        # 创建表格
        num_rows = len(table_data)
        num_cols = len(table_data[0]) if num_rows > 0 else 0
        
        if num_rows > 0 and num_cols > 0:
            word_table = doc.add_table(rows=num_rows, cols=num_cols)

            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement

            tbl = word_table._tbl
            tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')
            borders = OxmlElement('w:tblBorders')
            for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'single')
                border.set(qn('w:sz'), '4')
                border.set(qn('w:space'), '0')
                border.set(qn('w:color'), '000000')
                borders.append(border)
            tblPr.append(borders)

            for i, row in enumerate(table_data):
                for j, cell in enumerate(row):
                    cell_text = cell.text
                    cleaned_text = self._clean_xml_compatible_text(str(cell_text))
                    cell_paragraph = word_table.cell(i, j).paragraphs[0]
                    cell_run = cell_paragraph.add_run(cleaned_text)
                    cell_run.font.size = Pt(9)
            
            logger.info(f"添加表格成功，{num_rows}行{num_cols}列")
        else:
            logger.warning("表格数据格式不正确，跳过")