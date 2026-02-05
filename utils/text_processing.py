# 语义块合并逻辑

def _is_sentence_continuation(curr_text):
    """检查当前文本是否是前一个句子的延续
    
    Args:
        curr_text (str): 当前文本
        
    Returns:
        bool: 是否是前一个句子的延续
    """
    stripped_text = curr_text.strip()
    if not stripped_text:
        return False
    
    # 检查是否以小写字母开头（英语延续）
    if stripped_text[0].islower():
        return True
    
    # 检查是否以连字符、逗号或分号开头（句子内部标点）
    if stripped_text[0] in (',', ';', '-', '—', '、'):
        return True
    
    return False

def merge_semantic_blocks(text_blocks):
    """按语义合并文本块

    Args:
        text_blocks (list): 所有原始块列表（已按垂直位置排序，仅包含正文块）
                          每个元素是TextBlock对象

    Returns:
        tuple: (merged_blocks, block_mapping)
            merged_blocks: 合并后的语义块列表（MergedBlock对象列表）
            block_mapping: 原始块与合并块的映射关系
    """
    from models.merged_block import MergedBlock
    
    merged_blocks = []
    block_mapping = []  # 记录原始块与合并块的映射关系

    if not text_blocks:
        return merged_blocks, block_mapping

    # 获取第一个块的TextBlock对象和文本
    first_block = text_blocks[0]
    first_text_block = first_block
    first_bbox = first_text_block.block_bbox
    first_width = first_bbox[2] - first_bbox[0]  # x1 - x0
    first_height = first_bbox[3] - first_bbox[1]  # y1 - y0

    # 记录第一个块的信息
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"创建合并块，第一个原始块字体大小: {first_text_block.font_size}, 文本: '{first_text_block.block_text[:50]}...'")

    # 初始化当前合并块
    current_merged = MergedBlock(
        block_text=first_text_block.block_text,
        original_blocks=[first_block],  # 保留完整的块信息
        max_width=first_width,  # 初始化为第一个块的宽度
        max_height=first_height  # 初始化为第一个块的高度
    )
    
    for i in range(1, len(text_blocks)):
        # 通过索引i-1直接判断上一块（已按垂直位置排序）
        # prev_block_info = all_blocks[i-1]  # 上一块信息
        curr_block_info = text_blocks[i]    # 当前块信息
        curr_text_block = curr_block_info
        
        # 位置相邻检查（垂直距离小于阈值）
        # prev_bbox = prev_text_block.block_bbox
        curr_bbox = curr_text_block.block_bbox
        # vertical_distance = curr_bbox[1] - prev_bbox[3]  # y0 - previous y1
        
        # 内容完整检查（前一块不是完整句子结束）
        prev_merged_text = current_merged.block_text
        prev_ends_with_sentence = prev_merged_text.strip().endswith(('.', '!', '?', '。', '！', '？'))
        
        # 检查当前块是否延续前一个句子
        is_continuation = _is_sentence_continuation(curr_text_block.block_text)
        
        # 合并条件：
        # 前一块是不完整句子且当前块是其延续
        if (not prev_ends_with_sentence and is_continuation):
            # 合并块，处理空格
            prev_text = current_merged.block_text
            curr_text = curr_text_block.block_text
            
            # 检查前一个块是否以空格结尾，当前块是否以空格开头
            if prev_text.endswith(' ') and curr_text.startswith(' '):
                # 只保留一个空格
                current_merged.block_text = prev_text + curr_text[1:]
            elif not prev_text.endswith(' ') and not curr_text.startswith(' '):
                # 添加一个空格
                current_merged.block_text = prev_text + ' ' + curr_text
            else:
                # 直接拼接
                current_merged.block_text = prev_text + curr_text
            
            current_merged.original_blocks.append(curr_block_info)
            
            # 计算当前块的宽度和高度
            curr_width = curr_bbox[2] - curr_bbox[0]  # x1 - x0
            curr_height = curr_bbox[3] - curr_bbox[1]  # y1 - y0
            
            # 更新最大宽度和高度
            current_merged.max_width = max(current_merged.max_width, curr_width)
            current_merged.max_height = max(current_merged.max_height, curr_height)
        else:
            # 保存当前合并块
            merged_blocks.append(current_merged)
            block_mapping.append(current_merged.original_blocks)
            
            # 开始新的合并块
            curr_width = curr_bbox[2] - curr_bbox[0]  # x1 - x0
            curr_height = curr_bbox[3] - curr_bbox[1]  # y1 - y0
            current_merged = MergedBlock(
                block_text=curr_text_block.block_text,
                original_blocks=[curr_block_info],
                max_width=curr_width,
                max_height=curr_height
            )
    
    # 添加最后一个合并块（如果存在）
    if current_merged is not None:
        merged_blocks.append(current_merged)
        block_mapping.append(current_merged.original_blocks)
    
    return merged_blocks, block_mapping

# 辅助函数：检查字符是否为标点
def is_punctuation(char):
    """检查字符是否为标点符号
    
    Args:
        char (str): 要检查的字符
        
    Returns:
        bool: True如果是标点符号，否则False
    """
    punctuation = '.,;:?\"\'`~()[]{}<>|/\\-_=+@#$%^&*。，、；：？！“”‘’`~（）【】{}《》|/\＼－＿＝＋＠＃＄％＾＆＊'
    return char in punctuation

# 辅助函数：检查字符是否为单词边界
def is_word_boundary(char):
    """检查字符是否为单词边界
    
    Args:
        char (str): 要检查的字符
        
    Returns:
        bool: True如果是单词边界，否则False
    """
    # 单词边界包括空格、标点、换行符等
    # 但不包括连字符、撇号等单词内部字符
    if char in ['-', "'", '’', '`']:
        return False
    return char.isspace() or is_punctuation(char)

# 辅助函数：检查字符是否为不应该出现在句尾的左成对字符
def is_left_pair_character(char):
    """检查字符是否为不应该出现在句尾的左成对字符
    
    Args:
        char (str): 要检查的字符
        
    Returns:
        bool: True如果是左成对字符，否则False
    """
    # 包含所有应该避免出现在句尾的左成对字符，包括英文引号
    left_pair_chars = {'“', '‘', '（', '【', '｛', '《', '〈', '「', '『', '<', '(', '[', '"', "'"}
    return char in left_pair_chars


# 辅助函数：调整拆分位置，确保不拆分单词且标点不作为块首

def adjust_split_position(text, split_pos):
    """调整拆分位置，确保不拆分单词且标点不作为块首，同时充分利用分块长度
    
    Args:
        text (str): 要拆分的文本
        split_pos (int): 初始拆分位置
        
    Returns:
        int: 调整后的拆分位置
    """
    if split_pos <= 0 or split_pos >= len(text):
        return split_pos
    
    # 1. 确保拆分位置在有效范围内
    split_pos = max(1, min(split_pos, len(text) - 1))
    original_pos = split_pos
    
    # 2. 检查是否需要保护英文单词
    def is_english_word_char(c):
        return c.isalpha() or c in ['-', "'", '’', '`']
    
    # 优先考虑充分利用分块长度，只在必要时调整
    # 检查当前位置是否在英文单词内部
    if (split_pos > 0 and split_pos < len(text)):
        # 检查前后字符是否都是英文单词字符
        prev_char_is_word = is_english_word_char(text[split_pos-1])
        curr_char_is_word = is_english_word_char(text[split_pos])
        
        if prev_char_is_word and curr_char_is_word:
            # 当前位置在英文单词内部，需要调整
            
            # 向后寻找单词边界，优先充分利用分块长度
            next_boundary = split_pos
            while next_boundary < len(text) and is_english_word_char(text[next_boundary]):
                next_boundary += 1
            
            # 向前寻找单词边界
            prev_boundary = split_pos - 1
            while prev_boundary > 0 and is_english_word_char(text[prev_boundary]):
                prev_boundary -= 1
            
            # 计算与原始位置的距离，选择更接近的边界
            # 优先选择向后边界，充分利用分块长度
            next_dist = abs(next_boundary - original_pos)
            prev_dist = abs(prev_boundary - original_pos)
            
            # 如果向后调整不超过最大范围，优先选择向后边界
            if next_dist <= 10:
                split_pos = next_boundary
            elif prev_dist <= 10:
                split_pos = prev_boundary
            else:
                # 调整范围过大，选择更接近原始位置的边界
                split_pos = prev_boundary if prev_dist <= next_dist else next_boundary
        elif prev_char_is_word and not curr_char_is_word:
            # 当前位置是单词结束位置，不需要调整
            pass
        elif not prev_char_is_word and curr_char_is_word:
            # 当前位置是单词开始位置，不需要调整
            pass
    
    # 3. 确保下一个块的开头不是标点
    # 只向前调整，充分利用分块长度
    while split_pos < len(text) and is_punctuation(text[split_pos]):
        split_pos += 1
        # 确保不超过文本长度和最大调整范围
        if split_pos >= len(text) or split_pos - original_pos > 10:
            break
    
    # 4. 确保拆分位置前的字符不是左成对字符（不应出现在句尾）
    # 向后调整，确保充分利用分块长度
    adjustment_count = 0
    while split_pos < len(text) - 1 and is_left_pair_character(text[split_pos-1]):
        split_pos += 1
        adjustment_count += 1
        # 确保不超过最大调整范围
        if adjustment_count > 10:
            break
    
    # 5. 再次检查并确保拆分位置前的字符不是左成对字符
    # 如果向后调整不行，尝试向前调整
    if split_pos > 1 and is_left_pair_character(text[split_pos-1]):
        original_split_pos = split_pos
        adjustment_count = 0
        while split_pos > 1 and is_left_pair_character(text[split_pos-1]):
            split_pos -= 1
            adjustment_count += 1
            if adjustment_count > 10:
                break
    
    # 6. 确保拆分位置不超过文本长度
    split_pos = min(split_pos, len(text))
    
    # 7. 确保拆分位置至少为1
    return max(1, split_pos)

# 辅助函数：调整块首的标点，将其移到前一个块
def fix_block_start_punctuation(translated_blocks):
    """调整块首的标点，将其移到前一个块
    
    Args:
        translated_blocks (list): 拆分后的翻译块列表
        
    Returns:
        list: 调整后的翻译块列表
    """
    for i in range(1, len(translated_blocks)):
        current_block = translated_blocks[i]
        if not current_block:
            continue
        
        # 检查当前块首是否为标点
        while current_block and is_punctuation(current_block[0]):
            # 将标点移到前一个块末尾
            translated_blocks[i-1] += current_block[0]
            current_block = current_block[1:]
            translated_blocks[i] = current_block
            
            # 如果当前块为空，退出循环
            if not current_block:
                break
    
    return translated_blocks

# 结果拆分映射逻辑

def split_translated_result(merged_translation, original_blocks):
    """将完整翻译结果按原文本块的长度比例拆分
    
    Args:
        merged_translation (str): 合并块的翻译结果
        original_blocks (list): 原始块列表（已按垂直位置排序，带有序号）
                               每个元素是包含'text_block'和'page_num'的字典
        
    Returns:
        list: 拆分后的翻译结果，与原始块一一对应
    """
    # 检查参数类型，修复可能的参数顺序问题
    if isinstance(merged_translation, list) and isinstance(original_blocks, str):
        # 参数顺序颠倒了，交换它们
        merged_translation, original_blocks = original_blocks, merged_translation
    
    num_blocks = len(original_blocks)
    
    if num_blocks == 0:
        return []
    
    translation_len = len(merged_translation)
    
    # 处理空翻译结果
    if translation_len == 0:
        return ['' for _ in original_blocks]
    
    # 处理单个块情况
    if num_blocks == 1:
        return [merged_translation.strip()]
    
    min_characters_per_block = 3  # 每个块至少分配3个字符
    translated_blocks = ['' for _ in range(num_blocks)]
    available_text = merged_translation
    
    # 计算更精确的每个块的长度分配
    # 使用动态分配策略，确保充分利用每个块的可用长度
    start_pos = 0
    remaining_len = translation_len
    remaining_blocks = num_blocks
    
    for i in range(num_blocks):
        # 动态计算当前块的目标长度：向上取整(剩余长度 / 剩余块数)
        # 这样可以确保后面的块也能获得合理的长度
        target_len = -(-remaining_len // remaining_blocks)
        
        # 计算当前块的结束位置
        end_pos = start_pos + target_len
        # 对于最后一个块，确保不超过文本长度
        if i == num_blocks - 1:
            end_pos = translation_len
        end_pos = min(end_pos, translation_len)  # 确保不超过文本长度
        
        # 调整拆分位置，确保英文单词完整性和标点正确位置
        # 这里会优先充分利用分块长度
        adjusted_end = adjust_split_position(available_text, end_pos)
        actual_end = adjusted_end
        
        # 确保至少分配min_characters_per_block个字符
        if actual_end - start_pos < min_characters_per_block:
            actual_end = min(start_pos + min_characters_per_block, translation_len)
        
        # 获取当前块文本
        current_text = available_text[start_pos:actual_end].strip()
        
        # 如果块不为空，确保块首不是标点符号
        if current_text and is_punctuation(current_text[0]):
            # 寻找块首的标点，将其移到前一个块（如果有前一个块）
            if i > 0:
                # 找到所有连续的开头标点
                punct_end = 0
                while punct_end < len(current_text) and is_punctuation(current_text[punct_end]):
                    punct_end += 1
                
                if punct_end > 0:
                    # 将标点移到前一个块
                    translated_blocks[i-1] += current_text[:punct_end]
                    current_text = current_text[punct_end:].strip()
                    # 重新计算实际结束位置
                    actual_end = start_pos + (punct_end + len(current_text))
        
        # 确保块尾不是左成对字符
        if current_text and is_left_pair_character(current_text[-1]):
            # 向前调整实际结束位置，直到块尾不是左成对字符
            adjusted_actual_end = actual_end - 1
            while adjusted_actual_end > start_pos and is_left_pair_character(available_text[adjusted_actual_end-1]):
                adjusted_actual_end -= 1
            # 重新获取当前块文本
            current_text = available_text[start_pos:adjusted_actual_end].strip()
            # 更新实际结束位置
            actual_end = adjusted_actual_end
        
        translated_blocks[i] = current_text
        
        # 确保当前块尾不是左成对字符
        # 这是直接的修复，确保当前块尾没有左成对字符
        if current_text and is_left_pair_character(current_text[-1]):
            # 如果当前不是最后一个块，将左成对字符移到下一个块
            if i < num_blocks - 1:
                # 将左成对字符移到下一个块的开头
                translated_blocks[i+1] = current_text[-1] + translated_blocks[i+1]
                # 从当前块中移除左成对字符
                translated_blocks[i] = current_text[:-1]
        
        # 更新剩余长度和剩余块数
        used_len = actual_end - start_pos
        remaining_len -= used_len
        remaining_blocks -= 1
        
        # 更新起始位置
        start_pos = actual_end
        
        # 如果已经到达文本末尾，跳出循环
        if start_pos >= translation_len:
            break
    
    # 处理可能的空块情况
    for i in range(num_blocks):
        if not translated_blocks[i].strip() and i > 0:
            # 当前块为空，尝试从后一个块获取内容
            if i < num_blocks - 1 and translated_blocks[i+1]:
                next_block = translated_blocks[i+1]
                # 从后一个块中分配一些内容到当前块
                split_point = len(next_block) // 2
                adjusted_split = adjust_split_position(next_block, split_point)
                translated_blocks[i] = next_block[:adjusted_split].strip()
                translated_blocks[i+1] = next_block[adjusted_split:].strip()
            elif translated_blocks[i-1]:
                # 后一个块也为空或不存在，尝试从前一个块获取内容
                prev_block = translated_blocks[i-1]
                if len(prev_block) > min_characters_per_block:
                    split_point = len(prev_block) // 2
                    adjusted_split = adjust_split_position(prev_block, split_point)
                    translated_blocks[i] = prev_block[adjusted_split:].strip()
                    translated_blocks[i-1] = prev_block[:adjusted_split].strip()
    
    # 确保块尾不是左成对字符
    for i in range(num_blocks - 1):
        current_block = translated_blocks[i]
        # 检查并修复当前块尾的左成对字符
        while current_block and is_left_pair_character(current_block[-1]):
            next_block = translated_blocks[i+1]
            # 将左成对字符移到下一个块的开头
            translated_blocks[i+1] = current_block[-1] + next_block
            # 从当前块中移除左成对字符
            current_block = current_block[:-1]
            translated_blocks[i] = current_block
            # 如果当前块为空，跳出循环
            if not current_block:
                break
    
    # 最后调整标点，确保所有块首都不是标点
    translated_blocks = fix_block_start_punctuation(translated_blocks)
    
    # 最终检查：确保所有块尾都不是左成对字符
    # 这是最后的防线，确保所有块尾都没有左成对字符
    for i in range(num_blocks - 1):
        current_block = translated_blocks[i]
        # 确保current_block非空
        if not current_block:
            continue
        # 检查并修复当前块尾的左成对字符
        while current_block and is_left_pair_character(current_block[-1]):
            next_block = translated_blocks[i+1]
            # 将左成对字符移到下一个块的开头
            translated_blocks[i+1] = current_block[-1] + next_block
            # 从当前块中移除左成对字符
            current_block = current_block[:-1]
            translated_blocks[i] = current_block
            # 如果当前块为空，跳出循环
            if not current_block:
                break
    
    # 添加最终的分段长度平衡调整
    # 检查所有分段的长度，确保分布均匀
    if num_blocks > 1:
        # 计算各分段长度
        block_lengths = [len(block) for block in translated_blocks]
        
        # 计算平均长度和标准差
        avg_length = sum(block_lengths) / num_blocks
        max_length = max(block_lengths)
        
        # 如果最后一个分段明显长于平均长度，进行调整
        if block_lengths[-1] > avg_length * 1.5:
            # 计算需要重新分配的字符数
            excess_length = block_lengths[-1] - int(avg_length)
            
            # 从最后一个分段中取出多余的部分
            last_block = translated_blocks[-1]
            if excess_length > 0 and len(last_block) > excess_length:
                # 寻找合适的拆分位置，确保不拆分单词和左成对字符
                split_point = len(last_block) - excess_length
                adjusted_split = adjust_split_position(last_block, split_point)
                
                # 将多余部分分配到前面的分段中
                excess_text = last_block[adjusted_split:]
                translated_blocks[-1] = last_block[:adjusted_split]
                
                # 均匀分配到前面的分段
                num_front_blocks = num_blocks - 1
                if num_front_blocks > 0:
                    chars_per_block = len(excess_text) // num_front_blocks
                    remaining_chars = len(excess_text) % num_front_blocks
                    
                    current_pos = 0
                    for i in range(num_front_blocks):
                        # 计算当前块应分配的字符数
                        assign_chars = chars_per_block + (1 if i < remaining_chars else 0)
                        
                        # 如果还有剩余字符，分配给当前块
                        if current_pos < len(excess_text):
                            end_pos = current_pos + assign_chars
                            translated_blocks[i] += excess_text[current_pos:end_pos]
                            current_pos = end_pos
    
    return translated_blocks
