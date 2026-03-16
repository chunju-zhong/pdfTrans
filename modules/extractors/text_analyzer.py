import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

def calculate_text_similarity(text1, text2):
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
    lcs_len = _lcs_length(text1, text2)
    
    # 计算相似度
    max_len = max(len(text1), len(text2))
    similarity = lcs_len / max_len if max_len > 0 else 0.0
    
    return similarity

def _lcs_length(s1, s2):
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

def _add_similar_blocks(block_list1, block_list2, processed_pairs, non_body_texts):
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
            if page1 == page2 and hasattr(block1, 'block_no') and hasattr(block2, 'block_no') and block1.block_no == block2.block_no:
                continue
                
            # 避免重复处理同一对文本块
            pair_key = tuple(sorted([block1.block_text, block2.block_text]))
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            
            # 计算文本相似度
            similarity = calculate_text_similarity(block1.block_text, block2.block_text)
            
            if similarity >= 0.9:
                non_body_texts.add(block1.block_text)
                non_body_texts.add(block2.block_text)
                logger.debug(f"相似度识别为页眉页脚: 页面{page1} '{block1.block_text}' 与 页面{page2} '{block2.block_text}'，相似度: {similarity:.2f}")

def identify_header_footer(pages, page_sizes=None):
    """识别页眉和页脚
    
    Args:
        pages (list): 所有页面的文本块列表
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
        frequency_threshold = len(pages) * 0.7  # 超过70%的页面出现
        
        # 收集顶部和底部区域的文本
        top_bottom_texts = set()
        for page_num, block in top_blocks:
            top_bottom_texts.add(block.block_text)
        for page_num, block in bottom_blocks:
            top_bottom_texts.add(block.block_text)
        
        # 识别重复出现的文本块，只考虑顶部和底部区域的文本
        for text, count in block_frequency.items():
            if count >= frequency_threshold and text in top_bottom_texts:
                non_body_texts.add(text)
                logger.debug(f"多页PDF，识别为页眉页脚: '{text}'，出现次数: {count}")
    
    # 识别顶部15%和底部15%区域中文本重复率为90%的文本块
    # 比较顶部和底部区域的所有文本块对
    processed_pairs = set()
    
    # 比较顶部区域内部的文本块
    _add_similar_blocks(top_blocks, top_blocks, processed_pairs, non_body_texts)
    # 比较底部区域内部的文本块
    _add_similar_blocks(bottom_blocks, bottom_blocks, processed_pairs, non_body_texts)
    # 比较顶部和底部区域之间的文本块
    _add_similar_blocks(top_blocks, bottom_blocks, processed_pairs, non_body_texts)
    
    return non_body_texts

def identify_page_numbers(pages, page_sizes=None):
    """识别页码
    
    Args:
        pages (list): 所有页面的文本块列表
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
            block_font_size = getattr(block, 'font_size', 0)
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

def mark_non_body_text(pages, page_sizes=None, enable=True):
    """标记非正文文本块
    
    Args:
        pages (list): 所有页面的文本块列表
        page_sizes (dict): 页面尺寸字典，键为页码，值为页面尺寸 (width, height)
        enable (bool): 是否启用标记，默认为True
    """
    if not enable:
        logger.info("非正文文本块标记已禁用")
        return
    logger.info(f"开始标记非正文文本块，处理{len(pages)}个页面")
    
    # 识别页眉页脚
    logger.info("开始识别页眉页脚...")
    header_footer_set = identify_header_footer(pages, page_sizes)
    logger.info(f"页眉页脚识别完成，识别到{len(header_footer_set)}个文本块")
    for text in header_footer_set:
        logger.info(f"  页眉/页脚: '{text}'")
    
    # 识别页码
    logger.info("开始识别页码...")
    page_number_set = identify_page_numbers(pages, page_sizes)
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
            if getattr(block, 'is_body_text', True):
                body_blocks_before += 1
    logger.info(f"标记前: 总文本块={total_blocks_before}, 正文文本块={body_blocks_before}, 非正文文本块={total_blocks_before - body_blocks_before}")
    
    # 标记非正文文本块
    total_marked = 0
    for pdf_page in pages:
        page_marked = 0
        logger.debug(f"处理第{pdf_page.page_num}页，共{len(pdf_page.text_blocks)}个文本块")
        for block in pdf_page.text_blocks:
            original_status = getattr(block, 'is_body_text', True)
            if block.block_text in non_body_texts:
                block.is_body_text = False
                page_marked += 1
                total_marked += 1
                logger.info(f"页面{pdf_page.page_num} 块{block.block_no if hasattr(block, 'block_no') else 'N/A'} 从{'正文' if original_status else '非正文'}标记为非正文: '{block.block_text}'")
                logger.debug(f"  标记原因: {'页眉/页脚' if block.block_text in header_footer_set else '页码'}")
                logger.debug(f"  位置: {block.block_bbox}, 字体大小: {getattr(block, 'font_size', 'N/A')}, 字体: {getattr(block, 'font', 'N/A')}")
            else:
                if not original_status:
                    block.is_body_text = True
                    logger.info(f"页面{pdf_page.page_num} 块{block.block_no if hasattr(block, 'block_no') else 'N/A'} 从非正文恢复为正文: '{block.block_text}'")
                    logger.debug(f"  位置: {block.block_bbox}, 字体大小: {getattr(block, 'font_size', 'N/A')}, 字体: {getattr(block, 'font', 'N/A')}")
        if page_marked > 0:
            logger.info(f"第{pdf_page.page_num}页: 标记了{page_marked}个非正文文本块")
    
    # 统计标记后的正文/非正文文本块数量
    total_blocks_after = 0
    body_blocks_after = 0
    for pdf_page in pages:
        for block in pdf_page.text_blocks:
            total_blocks_after += 1
            if getattr(block, 'is_body_text', True):
                body_blocks_after += 1
    logger.info(f"标记后: 总文本块={total_blocks_after}, 正文文本块={body_blocks_after}, 非正文文本块={total_blocks_after - body_blocks_after}")
    logger.info(f"非正文文本块标记完成，共标记了{total_marked}个文本块")
