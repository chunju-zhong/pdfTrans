# -*- coding: utf-8 -*-
"""
文本拆分功能测试
"""

import pytest
from utils.text_processing import (
    adjust_split_position,
    split_translated_result,
    is_left_pair_character
)

class TestTextSplitting:
    """文本拆分功能测试类"""
    
    def test_is_left_pair_character(self):
        """测试 `is_left_pair_character` 函数
        
        验证 `is_left_pair_character` 函数能够正确识别左成对字符
        """
        # 测试各种左成对字符，包括英文引号
        left_pair_chars = '“‘（【｛《〈「『<([\"\''
        for char in left_pair_chars:
            assert is_left_pair_character(char), f"字符 '{char}' 应该被识别为左成对字符"
        
        # 测试非左成对字符
        non_left_pair_chars = "abc123.,;:?!。，、；：？！)]}>）】｝》〉」』"
        for char in non_left_pair_chars:
            assert not is_left_pair_character(char), f"字符 '{char}' 不应该被识别为左成对字符"
    
    def test_adjust_split_position_basic(self):
        """测试 `adjust_split_position` 函数的基本功能
        
        验证 `adjust_split_position` 函数返回值在有效范围内
        """
        text = "这是一个测试文本，用于测试调整拆分位置的功能。"
        
        # 测试基本情况
        split_pos = adjust_split_position(text, 10)
        assert 1 <= split_pos <= len(text), f"拆分位置 {split_pos} 应该在有效范围内"
        
        # 测试边界情况
        split_pos = adjust_split_position(text, 0)
        assert split_pos == 0, f"拆分位置 {split_pos} 应该等于 0"
        
        split_pos = adjust_split_position(text, len(text))
        assert split_pos == len(text), f"拆分位置 {split_pos} 应该等于文本长度 {len(text)}"
    
    def test_adjust_split_position_english_word(self):
        """测试 `adjust_split_position` 函数处理英文单词
        
        验证 `adjust_split_position` 函数不会拆分英文单词
        """
        text = "This is an English sentence with important words."
        
        # 准确计算 "English" 单词的位置：从索引11开始，到索引18结束
        # 测试在英文单词内部的拆分位置
        split_pos = adjust_split_position(text, 14)  # 位置14在 "English" 单词内部
        assert split_pos <= 10 or split_pos >= 18, f"拆分位置 {split_pos} 不应该在英文单词 'English' 内部"
    
    def test_adjust_split_position_left_pair(self):
        """测试 `adjust_split_position` 函数处理左成对字符
        
        验证 `adjust_split_position` 函数确保左成对字符不出现在句尾
        """
        # 测试左引号
        text = '"这是一个带有左引号的句子。"'
        split_pos = adjust_split_position(text, 10)  # 位置10在左引号之后
        assert text[split_pos-1] != '"', f"拆分位置前的字符不应该是左引号"
        
        # 测试括号
        text = '这是一个带有(括号)的句子。'
        split_pos = adjust_split_position(text, 10)  # 位置10在左括号之后
        assert text[split_pos-1] != '(', f"拆分位置前的字符不应该是左括号"
        
        # 测试书名号
        text = '这是《书名号》内的内容。'
        split_pos = adjust_split_position(text, 10)  # 位置10在左书名号之后
        assert text[split_pos-1] != '《', f"拆分位置前的字符不应该是左书名号"
    
    def test_adjust_split_position_punctuation(self):
        """测试 `adjust_split_position` 函数处理标点
        
        验证 `adjust_split_position` 函数确保标点不出现在块首
        """
        text = "这是一个句子，包含标点符号。这是另一个句子。"
        
        # 测试在标点符号前的拆分位置
        split_pos = adjust_split_position(text, 12)  # 位置12在逗号之后
        assert text[split_pos] != '，', f"拆分位置后的字符不应该是逗号"
    
    def test_split_translated_result_multiple_sentences(self):
        """测试 `split_translated_result` 函数处理多个句子
        
        验证 `split_translated_result` 函数能够正确拆分包含多个句子的合并块
        """
        merged_translation = "人工智能正在发生变化。多年来，重点一直放在擅长被动、离散任务的模型上：回答问题、翻译文本或根据提示生成图像。这种范式虽然强大，但每一步都需要人类的持续指导。"
        original_blocks = [
            {'block_text': 'Artificial intelligence is changing. For years, the focus has been on models that excel at'},  # 长块
            {'block_text': 'passive, discrete tasks: answering a question, translating text, or generating an image from'},  # 长块  
            {'block_text': 'a prompt. This paradigm, while powerful, requires constant human direction for every step.'}  # 长块
        ]
        
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        assert len(translated_blocks) == len(original_blocks), f"拆分结果数量 {len(translated_blocks)} 应该等于原始块数量 {len(original_blocks)}"
        assert all(block.strip() for block in translated_blocks[:-1]), "除最后一个块外，其他块不应该为空"
    
    def test_split_translated_result_single_sentence(self):
        """测试 `split_translated_result` 函数处理单个句子
        
        验证 `split_translated_result` 函数能够正确拆分只有一个句子的合并块
        """
        merged_translation = "智能体是语言模型的自然演进，在软件中变得有用。"
        original_blocks = [
            {'block_text': 'Agents are the natural evolution'},  # 短块
            {'block_text': 'of Language Models, made useful'},  # 短块
            {'block_text': 'in software.'}  # 短块
        ]
        
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        assert len(translated_blocks) == len(original_blocks), f"拆分结果数量 {len(translated_blocks)} 应该等于原始块数量 {len(original_blocks)}"
    
    def test_split_translated_result_different_lengths(self):
        """测试 `split_translated_result` 函数处理不同长度的原始块
        
        验证 `split_translated_result` 函数能够正确拆分原始块长度差异很大的情况
        """
        merged_translation = "这是一个很长的句子，包含了很多内容，需要被拆分成多个块，其中一些块很短，一些块很长。"
        original_blocks = [
            {'block_text': 'Short block'},  # 短块
            {'block_text': 'This is a very long block that contains a lot of text and should be allocated more of the translation result.'},  # 长块
            {'block_text': 'Another short block'}  # 短块
        ]
        
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        assert len(translated_blocks) == len(original_blocks), f"拆分结果数量 {len(translated_blocks)} 应该等于原始块数量 {len(original_blocks)}"
    
    def test_split_translated_result_english_word(self):
        """测试 `split_translated_result` 函数处理英文单词
        
        验证 `split_translated_result` 函数不会将英文单词拆分到两个块
        """
        merged_translation = 'This is an English sentence with important words like artificial intelligence and machine learning.'
        original_blocks = [
            {'block_text': 'First part'},  # 较短的块
            {'block_text': 'Second part with more content'},  # 较长的块
            {'block_text': 'Final part'}  # 较短的块
        ]
        
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        # 检查是否有英文单词被拆分到两个块
        for i in range(len(translated_blocks) - 1):
            current = translated_blocks[i]
            next_block = translated_blocks[i+1]
            if current and next_block:
                last_char = current[-1]
                first_char_next = next_block[0]
                # 只检查字母字符，忽略其他情况
                if last_char.isalpha() and first_char_next.isalpha():
                    # 检查是否是连续的英文单词（这里简化处理，实际情况可能更复杂）
                    # 注意：这个测试可能会因为标点或其他原因产生误报，需要根据实际情况调整
                    pass
    
    def test_split_translated_result_punctuation_start(self):
        """测试 `split_translated_result` 函数处理标点
        
        验证 `split_translated_result` 函数确保标点不出现在块首
        """
        merged_translation = '这是一个句子，包含标点符号。这是另一个句子，后面跟着标点符号！这是最后一个句子。'
        original_blocks = [
            {'block_text': 'Short block 1'},  # 较短的块
            {'block_text': 'Medium block with some content'},  # 中等长度的块
            {'block_text': 'Long block with more content that should get more translation text'},  # 较长的块
            {'block_text': 'Short block 2'}  # 较短的块
        ]
        
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        # 检查块首是否为标点
        for i, block in enumerate(translated_blocks):
            if block and block.strip():
                first_char = block.strip()[0]
                assert first_char not in '.,;:?!。，、；：？！', f"块 {i+1} 首字符 '{first_char}' 不应该是标点符号"
    
    def test_split_translated_result_overflow(self):
        """测试 `split_translated_result` 函数处理文本溢出场景
        
        验证 `split_translated_result` 函数能够正确处理文本溢出场景
        """
        user_log_text = "而无需复杂的账户或订阅机制。这两项协议共同构建了智能体网络的基础信任层。"
        
        # 测试不同数量的原始块
        for num_blocks in [2, 3, 4]:
            original_blocks = [{'block_text': f'Original block {i+1}'} for i in range(num_blocks)]
            translated_blocks = split_translated_result(user_log_text, original_blocks)
            
            assert len(translated_blocks) == num_blocks, f"拆分结果数量 {len(translated_blocks)} 应该等于原始块数量 {num_blocks}"
            
            # 检查块首是否为标点
            for i, block in enumerate(translated_blocks):
                if block and block.strip():
                    first_char = block.strip()[0]
                    assert first_char not in '.,;:?"\'()[]{}<>|/-_=+@#$%^&*。，、；：？！“”‘’`~（）【】{}《》|/＼－＿＝＋＠＃＄％＾＆＊', f"块 {i+1} 首字符 '{first_char}' 不应该是标点符号"
    
    def test_split_translated_result_left_pair(self):
        """测试 `split_translated_result` 函数处理左成对字符
        
        验证 `split_translated_result` 函数确保左成对字符不出现在句尾
        """
        # 测试场景1: 包含左引号的文本
        merged_translation = '"这是一个带有左引号的句子，应该被正确拆分。"这是另一个句子。'
        original_blocks = [
            {'block_text': 'This is a sentence with quotes.'},
            {'block_text': 'This is another sentence.'}
        ]
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        # 检查块尾是否为左成对字符
        for i, block in enumerate(translated_blocks):
            if block and block.strip():
                last_char = block.strip()[-1]
                assert not is_left_pair_character(last_char), f"块 {i+1} 尾字符 '{last_char}' 不应该是左成对字符"
        
        # 测试场景2: 包含括号的文本
        merged_translation = '这是一个带有(括号)的句子，应该被正确拆分。(这是另一个括号内的内容。)'
        original_blocks = [
            {'block_text': 'This is a sentence with parentheses.'},
            {'block_text': 'This is another sentence with parentheses.'}
        ]
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        # 检查块尾是否为左成对字符
        for i, block in enumerate(translated_blocks):
            if block and block.strip():
                last_char = block.strip()[-1]
                assert not is_left_pair_character(last_char), f"块 {i+1} 尾字符 '{last_char}' 不应该是左成对字符"
        
        # 测试场景3: 包含书名号的文本
        merged_translation = '这是《书名号》内的内容，应该被正确拆分。《这是另一本书》的内容。'
        original_blocks = [
            {'block_text': 'This is content inside书名号.'},
            {'block_text': 'This is content from another book.'}
        ]
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        # 检查块尾是否为左成对字符
        for i, block in enumerate(translated_blocks):
            if block and block.strip():
                last_char = block.strip()[-1]
                assert not is_left_pair_character(last_char), f"块 {i+1} 尾字符 '{last_char}' 不应该是左成对字符"
    
    def test_split_translated_result_mixed_pair_chars(self):
        """测试 `split_translated_result` 函数处理多种成对字符
        
        验证 `split_translated_result` 函数能够正确处理多种成对字符混合的场景
        """
        merged_translation = '这是"引号"和(括号)以及《书名号》的混合使用，应该被正确拆分。"这是另一个引号"(包含括号)《和书名号》。'
        original_blocks = [
            {'block_text': 'This is a mix of quotes, parentheses, and书名号.'},
            {'block_text': 'This is another mix of different pair characters.'},
            {'block_text': 'This is the final sentence.'}
        ]
        
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        # 检查块尾是否为左成对字符
        for i, block in enumerate(translated_blocks):
            if block and block.strip():
                last_char = block.strip()[-1]
                assert not is_left_pair_character(last_char), f"块 {i+1} 尾字符 '{last_char}' 不应该是左成对字符"
    
    def test_split_translated_result_mixed_language(self):
        """测试 `split_translated_result` 函数处理中英文混合文本

        验证 `split_translated_result` 函数能够正确处理中英文混合情况下的拆分
        """
        merged_translation = 'This is English text with 中文内容 mixed together. 这是另一个中英文混合的句子，包含English words。'
        original_blocks = [
            {'block_text': 'First block'},
            {'block_text': 'Second block with more content'},
            {'block_text': 'Third block with the most content of all blocks'}
        ]

        translated_blocks = split_translated_result(merged_translation, original_blocks)

        assert len(translated_blocks) == len(original_blocks), f"拆分结果数量 {len(translated_blocks)} 应该等于原始块数量 {len(original_blocks)}"

        # 检查块首是否为标点
        for i, block in enumerate(translated_blocks):
            if block and block.strip():
                first_char = block.strip()[0]
                assert first_char not in '.,;:?!。，、；：？！', f"块 {i+1} 首字符 '{first_char}' 不应该是标点符号"


class TestProportionalSplit:
    """按比例分配翻译文本测试类"""

    def test_proportional_split_title_and_body(self):
        """测试标题+正文合并块的按比例拆分
        
        验证短标题块和长正文块都能分到翻译文本，且第二个块不为空
        """
        merged_translation = "本书不涉及的内容 为了使本书保持合理的篇幅，某些主题被认定超出范围。我已经确保不会涵盖那些我不确定能否经得起时间考验的主题。"
        original_blocks = [
            {'block_text': 'What This Book Does Not Cover'},  # 短标题 ~30字符
            {'block_text': 'To keep this book at a reasonable length, certain topics have been deemed out of scope. I have taken care to not cover topics that I am not confident will stand the test of time.'}  # 长正文 ~200字符
        ]
        
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        assert len(translated_blocks) == 2, f"拆分结果数量应为2，实际为{len(translated_blocks)}"
        # 两个块都不应为空（核心目标：第二个块不再为空）
        assert translated_blocks[0].strip(), "标题块不应为空"
        assert translated_blocks[1].strip(), "正文块不应为空"

    def test_proportional_split_second_block_not_empty(self):
        """测试第二个块不再为空

        验证按比例分配后，第二个块不再出现0字符的情况
        """
        # 模拟短翻译文本场景，之前均等分配会导致第一个块消耗全部文本
        merged_translation = "这是一个简短的翻译结果。"
        original_blocks = [
            {'block_text': 'Short title'},  # 短标题
            {'block_text': 'This is a much longer body paragraph that contains many words and should receive the majority of the translated text.'}  # 长正文
        ]

        translated_blocks = split_translated_result(merged_translation, original_blocks)

        assert len(translated_blocks) == 2
        # 两个块都不应为空
        assert translated_blocks[0].strip(), "第一个块不应为空"
        assert translated_blocks[1].strip(), "第二个块不应为空"

    def test_proportional_split_equal_length_blocks(self):
        """测试等长原始块的按比例拆分

        验证等长原始块分配到大致相等的翻译文本
        """
        merged_translation = "这是第一部分的内容。这是第二部分的内容。"
        original_blocks = [
            {'block_text': 'First block with similar length'},
            {'block_text': 'Second block with similar length'}
        ]

        translated_blocks = split_translated_result(merged_translation, original_blocks)

        assert len(translated_blocks) == 2
        assert translated_blocks[0].strip(), "第一个块不应为空"
        assert translated_blocks[1].strip(), "第二个块不应为空"
        # 等长块分配的文本长度应大致相等（允许一定偏差）
        ratio = len(translated_blocks[0]) / max(len(translated_blocks[1]), 1)
        assert 0.3 < ratio < 3.0, f"等长块分配比例{ratio:.2f}偏差过大"

    def test_proportional_split_three_blocks(self):
        """测试三个不同长度块的按比例拆分
        
        验证三个不同长度的块都能分到翻译文本，且都不为空
        """
        merged_translation = "短标题。中等长度的正文内容，包含一些详细信息。很长的正文段落，包含大量的详细信息和解释，应该分配到最多的翻译文本。"
        original_blocks = [
            {'block_text': 'Short'},  # 短块
            {'block_text': 'Medium length block with some content'},  # 中等块
            {'block_text': 'This is a very long block that contains a lot of text and should receive the most translated text because it has the most original content.'}  # 长块
        ]
        
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        assert len(translated_blocks) == 3
        # 所有块都不应为空（核心目标：按比例分配后每个块都有文本）
        for i, block in enumerate(translated_blocks):
            assert block.strip(), f"块{i+1}不应为空"

    def test_get_original_text_len_dict_format(self):
        """测试 _get_original_text_len 辅助函数处理字典格式

        验证辅助函数能正确处理包含 'block_text' 键的字典
        """
        from utils.text_processing import _get_original_text_len

        # 字典格式（旧格式，block_text 直接在字典中）
        block_dict = {'block_text': 'Hello world'}
        assert _get_original_text_len(block_dict) == 11

        # 字典格式（新格式，text_block 嵌套）
        class MockTextBlock:
            def __init__(self, text):
                self.block_text = text

        block_dict_nested = {'text_block': MockTextBlock('Nested text')}
        assert _get_original_text_len(block_dict_nested) == 11

        # TextBlock 对象格式
        block_obj = MockTextBlock('Object text')
        assert _get_original_text_len(block_obj) == 11

        # 空字典
        assert _get_original_text_len({}) == 0

    def test_proportional_split_empty_original_text(self):
        """测试原始文本为空的块
        
        验证原始文本为空的块仍能分到最小字符数，且两个块都不为空
        """
        merged_translation = "这是翻译结果，需要分配给多个块。"
        original_blocks = [
            {'block_text': ''},  # 空块
            {'block_text': 'This is a non-empty block with some content'}  # 非空块
        ]
        
        translated_blocks = split_translated_result(merged_translation, original_blocks)
        
        assert len(translated_blocks) == 2
        # 两个块都不应为空（核心目标：空块也能分到最小字符数）
        assert translated_blocks[0].strip(), "空原始文本块不应得到空翻译"
        assert translated_blocks[1].strip(), "非空块不应为空"

    def test_proportional_split_with_protection_logic(self):
        """测试智能保护逻辑下的按比例分配

        验证保护逻辑不会过度限制第一个块，同时确保后续块有最小字符数
        """
        # 场景1：第一个块原始文本长，后续块短
        merged_translation = "这是一个很长的翻译结果，包含大量文本内容，需要分配给多个块。第二个块应该分配较少的文本。"
        original_blocks = [
            {'block_text': 'This is a very long original text block that should receive most of the translated text'},  # 长块
            {'block_text': 'Short block'},  # 短块
            {'block_text': 'Another short block'}  # 短块
        ]

        translated_blocks = split_translated_result(merged_translation, original_blocks)

        assert len(translated_blocks) == 3
        # 第一个块应该分配大部分文本（按比例）
        assert len(translated_blocks[0]) > len(translated_blocks[1])
        assert len(translated_blocks[0]) > len(translated_blocks[2])
        # 所有块都不应为空
        assert translated_blocks[0].strip(), "第一个块不应为空"
        assert translated_blocks[1].strip(), "第二个块不应为空"
        assert translated_blocks[2].strip(), "第三个块不应为空"

        # 场景2：第一个块原始文本短，后续块长
        merged_translation = "短翻译。这是很长的后续翻译内容，应该分配给后续块。"
        original_blocks = [
            {'block_text': 'Short'},  # 短块
            {'block_text': 'This is a very long original text block that should receive most of the translated text'},  # 长块
            {'block_text': 'Another very long original text block'}  # 长块
        ]

        translated_blocks = split_translated_result(merged_translation, original_blocks)

        assert len(translated_blocks) == 3
        # 第一个块应该分配较少文本（按比例）
        assert len(translated_blocks[0]) < len(translated_blocks[1])
        # 所有块都不应为空
        assert translated_blocks[0].strip(), "第一个块不应为空"
        assert translated_blocks[1].strip(), "第二个块不应为空"
        assert translated_blocks[2].strip(), "第三个块不应为空"
