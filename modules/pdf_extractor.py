import fitz  # PyMuPDF
import pdfplumber
import os
import logging
import re
from collections import defaultdict
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
    
    def _lcs_length(self, s1, s2):
        """计算两个字符串的最长公共子序列长度
        
        Args:
            s1 (str): 第一个字符串
            s2 (str): 第二个字符串
        
        Returns:
            int: 最长公共子序列长度
        """
        m = len(s1)
        n = len(s2)
        # 初始化动态规划表
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # 填充动态规划表
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def _calculate_text_similarity(self, text1, text2):
        """计算两个文本的相似度
        
        Args:
            text1 (str): 第一个文本
            text2 (str): 第二个文本
        
        Returns:
            float: 相似度，范围0.0-1.0
        """
        # 转换为小写并去除空白字符
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        # 如果其中一个文本为空，返回0
        if not text1 or not text2:
            return 0.0
        
        # 计算最长公共子序列长度
        lcs_len = self._lcs_length(text1, text2)
        
        # 计算相似度
        max_len = max(len(text1), len(text2))
        similarity = lcs_len / max_len if max_len > 0 else 0.0
        
        return similarity
    
    def _add_similar_blocks(self, block_list1, block_list2, processed_pairs, non_body_texts):
        """比较两个列表中的文本块，将相似度超过90%的添加到非正文文本集合
        
        Args:
            block_list1 (list): 第一个文本块列表，每个元素为 (page_num, block)
            block_list2 (list): 第二个文本块列表，每个元素为 (page_num, block)
            processed_pairs (set): 已处理的文本块对集合，用于避免重复处理
            non_body_texts (set): 非正文文本集合，用于存储识别的页眉页脚
        """
        for page1, block1 in block_list1:
            for page2, block2 in block_list2:
                # 跳过比较同一个块（相同页码和相同块编号）
                if page1 == page2 and block1.block_no == block2.block_no:
                    continue
                    
                # 避免重复处理同一对文本块
                pair_key = tuple(sorted([block1.block_text, block2.block_text]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                # 计算文本相似度
                similarity = self._calculate_text_similarity(block1.block_text, block2.block_text)
                
                if similarity >= 0.9:
                    non_body_texts.add(block1.block_text)
                    non_body_texts.add(block2.block_text)
                    logger.debug(f"相似度识别为页眉页脚: 页面{page1} '{block1.block_text}' 与 页面{page2} '{block2.block_text}'，相似度: {similarity:.2f}")
    
    def _identify_header_footer(self, pages, page_sizes=None):
        """识别页眉和页脚
        
        Args:
            pages (list[PdfPage]): 所有页面的文本块列表
            page_sizes (dict): 页面尺寸字典，键为页码，值为页面尺寸 (width, height)
        
        Returns:
            set: 识别为页眉或页脚的文本块内容集合
        """
        if not pages:
            return set()
        
        # 收集所有页面的文本块信息
        all_blocks = []
        block_frequency = defaultdict(int)
        # 按位置分组的文本块：顶部15%和底部15%
        top_blocks = []
        bottom_blocks = []
        
        logger.debug(f"页眉页脚识别: 页面数量={len(pages)}")
        
        # 收集所有文本块并统计频率
        for pdf_page in pages:
            page_num = pdf_page.page_num
            page_size = page_sizes.get(page_num, (0, 0))
            page_height = page_size[1] if page_size else 0
            
            for block in pdf_page.text_blocks:
                all_blocks.append((page_num, block))
                block_frequency[block.block_text] += 1
                
                # 根据位置分类文本块
                if page_height > 0:
                    block_y0, block_y1 = block.block_bbox[1], block.block_bbox[3]
                    # 顶部15%区域
                    if block_y1 < page_height * 0.15:
                        top_blocks.append((page_num, block))
                    # 底部15%区域
                    elif block_y0 > page_height * 0.85:
                        bottom_blocks.append((page_num, block))
        
        # 对于多页PDF，识别重复出现的文本块作为页眉页脚
        non_body_texts = set()
        if len(pages) > 1:
            # 计算出现频率阈值
            frequency_threshold = len(pages) * 0.5  # 超过50%的页面出现
            
            # 识别重复出现的文本块
            for text, count in block_frequency.items():
                if count >= frequency_threshold:
                    non_body_texts.add(text)
                    logger.debug(f"多页PDF，识别为页眉页脚: '{text}'，出现次数: {count}")
        
        # 识别顶部15%和底部15%区域中文本重复率为90%的文本块
        # 比较顶部和底部区域的所有文本块对
        processed_pairs = set()
        
        # 比较顶部区域内部的文本块
        self._add_similar_blocks(top_blocks, top_blocks, processed_pairs, non_body_texts)
        # 比较底部区域内部的文本块
        self._add_similar_blocks(bottom_blocks, bottom_blocks, processed_pairs, non_body_texts)
        # 比较顶部和底部区域之间的文本块
        self._add_similar_blocks(top_blocks, bottom_blocks, processed_pairs, non_body_texts)
        
        return non_body_texts
    
    def _identify_page_numbers(self, pages, page_sizes=None):
        """识别页码
        
        Args:
            pages (list[PdfPage]): 所有页面的文本块列表
            page_sizes (dict): 页面尺寸字典，键为页码，值为页面尺寸 (width, height)
        
        Returns:
            set: 识别为页码的文本块内容集合
        """
        if not pages:
            return set()
        
        # 收集所有页面的顶部和底部数字文本块
        potential_page_numbers = []
        
        logger.debug(f"页码识别: 页面数量={len(pages)}")
        
        # 正则表达式：匹配数字
        page_num_pattern = re.compile(r'\d+')
        
        # 收集所有可能的页码文本块
        for pdf_page in pages:
            page_num = pdf_page.page_num
            page_size = page_sizes.get(page_num, (0, 0))
            page_height = page_size[1] if page_size else 0
            
            for block in pdf_page.text_blocks:
                block_text = block.block_text
                block_font_size = block.font_size
                block_bbox = block.block_bbox
                
                # 跳过图表标题和表格标题
                if any(keyword in block_text for keyword in ["Figure", "Table"]):
                    logger.debug(f"页码识别：跳过图表/表格标题: '{block_text}'")
                    continue
                
                # 跳过参考文献引用格式的文本块（如：xxx:数字 或 xxx.数字）
                if re.search(r'\w+[:.]\d+', block_text):
                    logger.debug(f"页码识别：跳过参考文献引用: '{block_text}'")
                    continue
                
                # 检查是否包含数字
                if page_num_pattern.search(block_text):
                    # 尝试提取所有数字
                    numbers = page_num_pattern.findall(block_text)
                    for num in numbers:
                        try:
                            page_num_value = int(num)
                            
                            # 计算文本块位置，判断是否在页面顶部或底部区域
                            block_y0, block_y1 = block_bbox[1], block_bbox[3]
                            
                            # 检查文本块是否在页面的顶部或底部区域（15%高度内）
                            is_top_or_bottom = False
                            if page_height > 0:
                                # 顶部区域
                                if block_y1 < page_height * 0.15:
                                    is_top_or_bottom = True
                                # 底部区域
                                elif block_y0 > page_height * 0.85:
                                    is_top_or_bottom = True
                            
                            # 检查文本块是否几乎全是数字（独立页码）
                            # 数字占文本块长度的比例超过50%
                            text_length = len(block_text.strip())
                            num_length = len(num)
                            is_mainly_number = (num_length / text_length) > 0.5
                            
                            potential_page_numbers.append((
                                pdf_page.page_num, 
                                page_num_value, 
                                block_text, 
                                num,
                                block_font_size,
                                is_top_or_bottom,
                                is_mainly_number
                            ))
                            logger.debug(f"页面{pdf_page.page_num} 发现潜在页码: '{block_text}', 提取的数字: '{num}', 字体大小: {block_font_size}, 位置: {'顶部/底部' if is_top_or_bottom else '中间'}, 是否主要为数字: {is_mainly_number}")
                        except ValueError:
                            pass
        
        # 检查数字是否为页码
        page_number_set = set()
        if potential_page_numbers:
            # 对于单页PDF，识别包含数字的小字体文本块为页码
            if len(pages) == 1:
                for _, _, full_text, num, font_size, is_top_or_bottom, is_mainly_number in potential_page_numbers:
                    # 查找对应的文本块，综合考虑字体大小、位置和是否主要为数字
                    for pdf_page in pages:
                        for block in pdf_page.text_blocks:
                            if block.block_text == full_text:
                                # 小字体（<10.0）且位于顶部/底部区域且主要为数字的文本块更可能是页码
                                if font_size < 10.0 and is_top_or_bottom and is_mainly_number:
                                    page_number_set.add(full_text)
                                    logger.debug(f"单页PDF，识别页码: '{full_text}'")
            else:
                # 对于多页PDF，检查数字是否与页码匹配
                for page_num, num_value, full_text, num, font_size, is_top_or_bottom, is_mainly_number in potential_page_numbers:
                    # 检查条件：
                    # 1. 数字与页码匹配
                    # 2. 字体大小较小（<10.0）
                    # 3. 位于页面顶部或底部区域
                    # 4. 主要为数字
                    if num_value == page_num and font_size < 10.0 and is_top_or_bottom and is_mainly_number:
                        page_number_set.add(full_text)
                        logger.debug(f"识别为页码: '{full_text}' (页面{page_num}，页码值{num_value})")
                
                # 如果没有识别到页码，尝试检查连续递增的数字
                if not page_number_set:
                    # 按页码排序
                    potential_page_numbers.sort(key=lambda x: x[0])
                    
                    # 检查是否有连续递增的数字序列，且都位于页面边缘
                    continuous_numbers = []
                    for i in range(len(potential_page_numbers) - 1):
                        current_page, current_num, current_text, _, _, current_is_top, current_is_mainly_num = potential_page_numbers[i]
                        next_page, next_num, next_text, _, _, next_is_top, next_is_mainly_num = potential_page_numbers[i + 1]
                        
                        # 检查是否连续递增且页码也连续，且都位于页面边缘，且主要为数字
                        if (next_num == current_num + 1 and 
                            next_page == current_page + 1 and 
                            current_is_top and 
                            next_is_top and 
                            current_is_mainly_num and 
                            next_is_mainly_num):
                            if current_text not in continuous_numbers:
                                continuous_numbers.append(current_text)
                            if next_text not in continuous_numbers:
                                continuous_numbers.append(next_text)
                    
                    if continuous_numbers:
                        for text in continuous_numbers:
                            page_number_set.add(text)
                            logger.debug(f"根据连续递增模式识别页码: '{text}'")
        
        return page_number_set
    
    def _mark_non_body_text(self, pages, page_sizes=None):
        """标记非正文文本块
        
        Args:
            pages (list[PdfPage]): 所有页面的文本块列表
            page_sizes (dict): 页面尺寸字典，键为页码，值为页面尺寸 (width, height)
        """
        logger.info(f"开始标记非正文文本块，处理{len(pages)}个页面")
        
        # 识别页眉页脚
        logger.info("开始识别页眉页脚...")
        header_footer_set = self._identify_header_footer(pages, page_sizes)
        logger.info(f"页眉页脚识别完成，识别到{len(header_footer_set)}个文本块")
        for text in header_footer_set:
            logger.info(f"  页眉/页脚: '{text}'")
        
        # 识别页码
        logger.info("开始识别页码...")
        page_number_set = self._identify_page_numbers(pages, page_sizes)
        logger.info(f"页码识别完成，识别到{len(page_number_set)}个文本块")
        for text in page_number_set:
            logger.info(f"  页码: '{text}'")
        
        # 合并非正文文本块集合
        non_body_texts = header_footer_set.union(page_number_set)
        logger.info(f"总计识别到{len(non_body_texts)}个非正文文本块")
        logger.debug(f"非正文文本块集合: {non_body_texts}")
        
        # 统计标记前的正文/非正文文本块数量
        total_blocks_before = 0
        body_blocks_before = 0
        for pdf_page in pages:
            for block in pdf_page.text_blocks:
                total_blocks_before += 1
                if block.is_body_text:
                    body_blocks_before += 1
        logger.info(f"标记前: 总文本块={total_blocks_before}, 正文文本块={body_blocks_before}, 非正文文本块={total_blocks_before - body_blocks_before}")
        
        # 标记非正文文本块
        total_marked = 0
        for pdf_page in pages:
            page_marked = 0
            logger.debug(f"处理第{pdf_page.page_num}页，共{len(pdf_page.text_blocks)}个文本块")
            for block in pdf_page.text_blocks:
                original_status = block.is_body_text
                if block.block_text in non_body_texts:
                    block.is_body_text = False
                    page_marked += 1
                    total_marked += 1
                    logger.info(f"页面{pdf_page.page_num} 块{block.block_no} 从{'正文' if original_status else '非正文'}标记为非正文: '{block.block_text}'")
                    logger.debug(f"  标记原因: {'页眉/页脚' if block.block_text in header_footer_set else '页码'}")
                    logger.debug(f"  位置: {block.block_bbox}, 字体大小: {block.font_size}, 字体: {block.font}")
                else:
                    if not original_status:
                        block.is_body_text = True
                        logger.info(f"页面{pdf_page.page_num} 块{block.block_no} 从非正文恢复为正文: '{block.block_text}'")
                        logger.debug(f"  位置: {block.block_bbox}, 字体大小: {block.font_size}, 字体: {block.font}")
            if page_marked > 0:
                logger.info(f"第{pdf_page.page_num}页: 标记了{page_marked}个非正文文本块")
        
        # 统计标记后的正文/非正文文本块数量
        total_blocks_after = 0
        body_blocks_after = 0
        for pdf_page in pages:
            for block in pdf_page.text_blocks:
                total_blocks_after += 1
                if block.is_body_text:
                    body_blocks_after += 1
        logger.info(f"标记后: 总文本块={total_blocks_after}, 正文文本块={body_blocks_after}, 非正文文本块={total_blocks_after - body_blocks_after}")
        logger.info(f"非正文文本块标记完成，共标记了{total_marked}个文本块")
    
    def extract_text(self, pdf_path, pages=None):
        """提取PDF中的文本内容，可以指定页面

        Args:
            pdf_path (str): PDF文件路径
            pages (list[int] | None): 指定要提取的页码列表（从1开始），None表示提取所有页面
            
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
        
        # 存储页面尺寸信息
        page_sizes = {}
        
        try:
            logger.info(f"开始提取PDF: {pdf_path}")
            
            # 使用PyMuPDF提取普通文本和页面尺寸
            with fitz.open(pdf_path) as doc:
                result['total_pages'] = len(doc)
                logger.info(f"PDF总页数: {len(doc)}")
                
                # 处理页码参数
                all_pages = list(range(len(doc)))
                pages_to_process = all_pages
                
                if pages is not None:
                    # 去重并排序
                    unique_pages = sorted(set(pages))
                    # 转换为0-based索引并验证范围
                    valid_pages = []
                    for page in unique_pages:
                        if 1 <= page <= len(doc):
                            valid_pages.append(page - 1)  # 转换为0-based索引
                        else:
                            logger.warning(f"页码{page}超出范围（总页数: {len(doc)}），将被忽略")
                    pages_to_process = valid_pages
                    logger.info(f"指定提取的页码: {[p + 1 for p in pages_to_process]}")
                
                for page_num in pages_to_process:
                    page = doc[page_num]
                    
                    # 获取页面实际尺寸
                    page_rect = page.rect
                    page_sizes[page_num + 1] = (page_rect.width, page_rect.height)
                    logger.debug(f"页面{page_num + 1} 实际尺寸: {page_rect}")
                    
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
                    

            # 使用pdfplumber提取表格
            with pdfplumber.open(pdf_path) as pdf:
                # 确定需要提取表格的页面
                tables_pages_to_process = list(range(len(pdf.pages)))
                if pages is not None:
                    # 转换为0-based索引并验证范围
                    tables_pages_to_process = []
                    for page in sorted(set(pages)):
                        if 1 <= page <= len(pdf.pages):
                            tables_pages_to_process.append(page - 1)  # 转换为0-based索引
                
                for page_num in tables_pages_to_process:
                    page = pdf.pages[page_num]
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
            
            # 标记非正文文本块（页眉、页脚、页码）
            self._mark_non_body_text(pdf_pages, page_sizes)
            
            # 日志记录 - 移到标记非正文文本块之后
            for pdf_page in pdf_pages:
                logger.info(f"第{pdf_page.page_num}页: 提取到{len(pdf_page.text_blocks)}个文本块")
                for i, text_block in enumerate(pdf_page.text_blocks):
                    logger.info(f"第{pdf_page.page_num}页 文本块 {i+1}: '{text_block.block_text}' 位置: {text_block.block_bbox} 块编号: {text_block.block_no} 字体: {text_block.font} 大小: {text_block.font_size} 粗体: {text_block.bold} 斜体: {text_block.italic} 是否为正文: {text_block.is_body_text}")
            
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
            
            # 获取页面实际尺寸
            page_rect = page.rect
            page_size = (page_rect.width, page_rect.height)
            page_sizes = {page_num: page_size}
            logger.debug(f"页面{page_num} 实际尺寸: {page_rect}")
            
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
            
            # 创建PdfPage对象
            pdf_page = PdfPage(
                page_num=page_num,
                text_blocks=sorted_text_blocks
            )
            
            # 标记非正文文本块
            self._mark_non_body_text([pdf_page], page_sizes)
            
            logger.info(f"页面{page_num}提取完成: 共{len(sorted_text_blocks)}个文本块")
            for i, text_block in enumerate(sorted_text_blocks):
                logger.info(f"第{page_num}页 文本块 {i+1}: '{text_block.block_text}' 位置: {text_block.block_bbox} 块编号: {text_block.block_no} 字体: {text_block.font} 大小: {text_block.font_size} 粗体: {text_block.bold} 斜体: {text_block.italic} 是否为正文: {text_block.is_body_text}")
            
            return pdf_page
    
    def extract_tables(self, pdf_path, pages=None):
        """仅提取PDF中的表格内容
        
        Args:
            pdf_path (str): PDF文件路径
            pages (list[int] | None): 指定要提取的页码列表（从1开始），None表示提取所有页面
            
        Returns:
            list[PdfTable]: 提取的表格列表
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        logger.info(f"开始提取表格: {pdf_path}")
        
        pdf_tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 处理页码参数
                total_pages = len(pdf.pages)
                all_pages = list(range(total_pages))
                pages_to_process = all_pages
                
                if pages is not None:
                    # 去重并排序
                    unique_pages = sorted(set(pages))
                    # 转换为0-based索引并验证范围
                    valid_pages = []
                    for page in unique_pages:
                        if 1 <= page <= total_pages:
                            valid_pages.append(page - 1)  # 转换为0-based索引
                        else:
                            logger.warning(f"页码{page}超出范围（总页数: {total_pages}），将被忽略")
                    pages_to_process = valid_pages
                    logger.info(f"指定提取表格的页码: {[p + 1 for p in pages_to_process]}")
                
                for page_num in pages_to_process:
                    page = pdf.pages[page_num]
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
    
    def extract_text_blocks(self, pdf_path, pages=None):
        """提取PDF中每个文本块的完整文本和位置

        确保文段完整性，适合整体翻译

        Args:
            pdf_path (str): PDF文件路径
            pages (list[int] | None): 指定要提取的页码列表（从1开始），None表示提取所有页面
            
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
        
        # 存储页面尺寸信息
        page_sizes = {}
        
        try:
            logger.info(f"开始提取文本块: {pdf_path}")
            
            with fitz.open(pdf_path) as doc:
                result['total_pages'] = len(doc)
                logger.info(f"PDF总页数: {len(doc)}")
                
                # 处理页码参数
                all_pages = list(range(len(doc)))
                pages_to_process = all_pages
                
                if pages is not None:
                    # 去重并排序
                    unique_pages = sorted(set(pages))
                    # 转换为0-based索引并验证范围
                    valid_pages = []
                    for page in unique_pages:
                        if 1 <= page <= len(doc):
                            valid_pages.append(page - 1)  # 转换为0-based索引
                        else:
                            logger.warning(f"页码{page}超出范围（总页数: {len(doc)}），将被忽略")
                    pages_to_process = valid_pages
                    logger.info(f"指定提取的页码: {[p + 1 for p in pages_to_process]}")
                
                for page_num in pages_to_process:
                    page = doc[page_num]
                    
                    # 获取页面实际尺寸
                    page_rect = page.rect
                    page_sizes[page_num + 1] = (page_rect.width, page_rect.height)
                    logger.debug(f"页面{page_num + 1} 实际尺寸: {page_rect}")
                    
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
            
            logger.info(f"提取文本块完成，总页数: {result['total_pages']}")
            
            # 标记非正文文本块（页眉、页脚、页码）
            self._mark_non_body_text(result['pages'], page_sizes)
            
            # 日志记录 - 移到标记非正文文本块之后
            for pdf_page in result['pages']:
                logger.info(f"第{pdf_page.page_num}页: 提取到{len(pdf_page.text_blocks)}个文本块")
                for i, text_block in enumerate(pdf_page.text_blocks):
                    logger.info(f"第{pdf_page.page_num}页 文本块 {i+1}: '{text_block.block_text}' 位置: {text_block.block_bbox} 块编号: {text_block.block_no} 字体: {text_block.font} 大小: {text_block.font_size} 粗体: {text_block.bold} 斜体: {text_block.italic} 是否为正文: {text_block.is_body_text}")
            
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
