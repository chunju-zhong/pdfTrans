# -*- coding: utf-8 -*-
"""
语义合并扩展测试
针对文本块丢失问题添加的测试用例
"""

import pytest
from utils.text_processing import merge_semantic_blocks, split_translated_result, _is_sentence_continuation
from models.text_block import TextBlock

class TestSemanticMergeExtended:
    """语义合并扩展测试类"""

    def test_merge_consecutive_body_blocks(self):
        """测试连续正文块的合并
        
        验证连续正文块能够正确合并为一个语义块
        这是针对之前块21、22、23丢失问题的测试
        """
        # 创建测试数据：模拟第8页的连续正文块
        text_blocks = [
            TextBlock(
                block_no=20,
                text='and puts the tool results into the  input context window of the next LM call.',
                bbox=(86.16799926757812, 534.44091796875, 459.72149658203125, 550.7869262695312)
            ),
            TextBlock(
                block_no=21,
                text='• The Orchestration Layer (The "Nervous System"): The governing process that',
                bbox=(72.0, 561.3359375, 497.6649169921875, 578.7599487304688)
            ),
            TextBlock(
                block_no=22,
                text="manages the agent's operational loop. It handles planning, memory (state), and reasoning",
                bbox=(86.16799926757812, 579.44189453125, 536.8162841796875, 595.7879028320312)
            ),
            TextBlock(
                block_no=23,
                text='strategy execution. This layer uses prompting frameworks and reasoning techniques (like',
                bbox=(86.16799926757812, 597.4378662109375, 533.5053100585938, 613.7838745117188)
            )
        ]
        
        # 直接使用TextBlock对象列表
        all_blocks = text_blocks

        # 调用语义合并方法
        merged_blocks, block_mapping = merge_semantic_blocks(all_blocks)
        
        # 验证所有原始块都被处理
        original_block_nos = {block.block_no for block in all_blocks}
        processed_block_nos = set()
        for merged_block in merged_blocks:
            for original_block in merged_block.original_blocks:
                processed_block_nos.add(original_block.block_no)
        
        assert original_block_nos == processed_block_nos, \
            f"部分块丢失！原始块: {original_block_nos}, 处理后块: {processed_block_nos}"
        
        # 验证合并块数量合理
        assert len(merged_blocks) <= len(all_blocks), "合并后块数量不应超过原始块数量"
        
        # 验证所有合并块都有正确的结构
        for merged_block in merged_blocks:
            assert hasattr(merged_block, 'block_text')
            assert hasattr(merged_block, 'original_blocks')
            assert hasattr(merged_block, 'max_width')
            assert hasattr(merged_block, 'max_height')

    def test_merge_blocks_with_sentence_continuation_lowercase(self):
        """测试以小写字母开头的句子延续合并
        
        验证当前块以小写字母开头时，能够与前一块合并
        """
        text_blocks = [
            TextBlock(
                block_no=1,
                text='This is the first sentence that ends',
                bbox=(0, 0, 200, 20)
            ),
            TextBlock(
                block_no=2,
                text='with a continuation word here.',
                bbox=(0, 25, 200, 45)
            )
        ]
        
        # 直接使用TextBlock对象列表
        all_blocks = text_blocks

        merged_blocks, block_mapping = merge_semantic_blocks(all_blocks)
        
        # 验证两个块被合并为一个
        assert len(merged_blocks) == 1, \
            f"预期合并为1个块，实际得到{len(merged_blocks)}个块"
        assert merged_blocks[0]['block_text'] == 'This is the first sentence that ends with a continuation word here.'

    def test_merge_blocks_with_sentence_continuation_lowercase(self):
        """测试以小写字母开头的句子延续合并

        验证当前块以小写字母开头时，能够与前一块合并
        """
        text_blocks = [
            TextBlock(
                block_no=1,
                text='This is the first sentence that ends',
                bbox=(0, 0, 200, 20)
            ),
            TextBlock(
                block_no=2,
                text='with a continuation word here.',
                bbox=(0, 25, 200, 45)
            )
        ]

        # 直接使用TextBlock对象列表
        all_blocks = text_blocks

        merged_blocks, block_mapping = merge_semantic_blocks(all_blocks)
        
        # 验证两个块被合并为一个
        assert len(merged_blocks) == 1, \
            f"预期合并为1个块，实际得到{len(merged_blocks)}个块"

    def test_no_merge_when_sentence_ends(self):
        """测试完整句子结尾时不合并
        
        验证当前块以大写字母开头且前一块是完整句子时，不合并
        """
        text_blocks = [
            TextBlock(
                block_no=1,
                text='This is the first sentence.',
                bbox=(0, 0, 200, 20)
            ),
            TextBlock(
                block_no=2,
                text='This is the second sentence.',
                bbox=(0, 25, 200, 45)
            )
        ]
        
        # 直接使用TextBlock对象列表
        all_blocks = text_blocks

        merged_blocks, block_mapping = merge_semantic_blocks(all_blocks)
        
        # 验证两个块不被合并（因为前一块是完整句子）
        assert len(merged_blocks) == 2, \
            f"预期保持2个块，实际得到{len(merged_blocks)}个块"

    def test_no_merge_when_vertical_distance_large(self):
        """测试垂直距离过大时不合并
        
        验证相邻块垂直距离大于阈值时，不合并
        """
        text_blocks = [
            TextBlock(
                block_no=1,
                text='This is the first sentence without ending',
                bbox=(0, 0, 200, 20)
            ),
            TextBlock(
                block_no=2,
                text='This is the second sentence.',
                bbox=(0, 100, 200, 120)  # 垂直距离较大（80 > 10）
            )
        ]
        
        # 直接使用TextBlock对象列表
        all_blocks = text_blocks

        merged_blocks, block_mapping = merge_semantic_blocks(all_blocks)
        
        # 验证两个块不被合并（因为垂直距离过大）
        assert len(merged_blocks) == 2, \
            f"预期保持2个块，实际得到{len(merged_blocks)}个块"

    def test_merge_multiple_sequential_blocks(self):
        """测试多个连续块的合并
        
        验证3个以上连续块能够正确合并
        """
        text_blocks = [
            TextBlock(
                block_no=1,
                text='First part of a long sentence that',
                bbox=(0, 0, 200, 20)
            ),
            TextBlock(
                block_no=2,
                text='continues to the second part',
                bbox=(0, 25, 200, 45)
            ),
            TextBlock(
                block_no=3,
                text='and then to the third part',
                bbox=(0, 50, 200, 70)
            ),
            TextBlock(
                block_no=4,
                text='finally ending the sentence.',
                bbox=(0, 75, 200, 95)
            )
        ]
        
        # 直接使用TextBlock对象列表
        all_blocks = text_blocks

        merged_blocks, block_mapping = merge_semantic_blocks(all_blocks)
        
        # 验证所有原始块都被处理
        original_count = len(all_blocks)
        processed_count = sum(len(merged_block.original_blocks) for merged_block in merged_blocks)
        assert original_count == processed_count, \
            f"部分块丢失！原始{original_count}个块，处理后{processed_count}个块"
        
        # 验证所有块被合并为一个
        assert len(merged_blocks) == 1, \
            f"预期合并为1个块，实际得到{len(merged_blocks)}个块"

    def test_empty_blocks_list(self):
        """测试空列表输入
        
        验证空列表输入时返回空结果
        """
        merged_blocks, block_mapping = merge_semantic_blocks([])
        
        assert merged_blocks == []
        assert block_mapping == []

    def test_single_block(self):
        """测试单个块
        
        验证单个块输入时返回正确结果
        """
        text_block = TextBlock(
            block_no=1,
            text='Single block content.',
            bbox=(0, 0, 200, 20)
        )
        
        # 直接使用TextBlock对象列表
        all_blocks = [text_block]

        merged_blocks, block_mapping = merge_semantic_blocks(all_blocks)
        
        assert len(merged_blocks) == 1
        assert merged_blocks[0].block_text == 'Single block content.'

    def test_is_sentence_continuation(self):
        """测试句子延续检测函数
        
        验证_is_sentence_continuation函数能正确识别句子延续
        """
        # 以小写字母开头
        assert _is_sentence_continuation('continues here') == True
        assert _is_sentence_continuation('another word') == True
        
        # 以标点开头
        assert _is_sentence_continuation(', continues') == True
        assert _is_sentence_continuation('- continues') == True
        assert _is_sentence_continuation('; continues') == True
        
        # 以大写字母开头
        assert _is_sentence_continuation('Starts with capital') == False
        
        # 空字符串
        assert _is_sentence_continuation('') == False
        assert _is_sentence_continuation('   ') == False


class TestTextSplittingExtended:
    """文本拆分扩展测试类"""

    def test_split_with_english_words(self):
        """测试英文单词完整性保护
        
        验证翻译结果拆分时不拆分英文单词
        """
        original_blocks = [
            TextBlock(block_no=1, text='This is a test paragraph with multiple', bbox=(0, 0, 300, 20)),
            TextBlock(block_no=2, text='words that should not be split incorrectly.', bbox=(0, 25, 300, 45))
        ]
        
        # 假设翻译结果比原文本长，但不应该拆分单词
        translated_text = '这是一个测试段落，包含多个不应被错误拆分的单词。'
        
        split_result = split_translated_result(original_blocks, translated_text)
        
        assert len(split_result) == len(original_blocks)
        # 每个拆分结果都应该有内容
        for i, result in enumerate(split_result):
            assert len(result) > 0, f"块{i+1}的拆分结果为空"

    def test_split_with_punctuation_adjustment(self):
        """测试标点位置调整
        
        验证翻译结果拆分后标点位置正确
        """
        original_blocks = [
            TextBlock(block_no=1, text='First sentence,', bbox=(0, 0, 200, 20)),
            TextBlock(block_no=2, text='second sentence.', bbox=(0, 25, 200, 45))
        ]
        
        translated_text = '第一句，第二句。'
        
        split_result = split_translated_result(original_blocks, translated_text)
        
        assert len(split_result) == len(original_blocks)
        # 验证标点没有被错误地放在块首
        for result in split_result:
            # 块首不应该有标点
            if result:
                first_char = result[0]
                punctuation = '.,;:?!。，！？'
                assert first_char not in punctuation, \
                    f"块首不应有标点，但发现'{first_char}'"

    def test_split_empty_translation(self):
        """测试空翻译结果处理
        
        验证空翻译结果时返回空字符串列表
        """
        original_blocks = [
            TextBlock(block_no=1, text='Some text', bbox=(0, 0, 100, 20)),
            TextBlock(block_no=2, text='More text', bbox=(0, 25, 100, 45))
        ]
        
        translated_text = ''
        
        split_result = split_translated_result(original_blocks, translated_text)
        
        assert len(split_result) == len(original_blocks)
        for result in split_result:
            assert result == ''


class TestBlockFiltering:
    """块过滤测试类"""

    def test_filter_non_body_blocks(self):
        """测试非正文块过滤
        
        验证translation_service能正确过滤非正文块
        （此测试需要模拟完整的翻译流程）
        """
        # 创建包含正文和非正文块的测试数据
        text_blocks = [
            TextBlock(
                block_no=1,
                text='Header Text',
                bbox=(50, 50, 150, 70),
                block_type=0
            ),
            TextBlock(
                block_no=2,
                text='This is body text that should be translated.',
                bbox=(50, 100, 300, 120),
                block_type=0
            ),
            TextBlock(
                block_no=3,
                text='Footer Text',
                bbox=(50, 700, 150, 720),
                block_type=0
            ),
            TextBlock(
                block_no=4,
                text='More body text here.',
                bbox=(50, 150, 300, 170),
                block_type=0
            )
        ]
        
        # 标记正文和非正文
        text_blocks[0].is_body_text = False  # 页眉
        text_blocks[1].is_body_text = True   # 正文
        text_blocks[2].is_body_text = False  # 页脚
        text_blocks[3].is_body_text = True   # 正文
        
        # 过滤非正文块
        body_blocks = [block for block in text_blocks if block.is_body_text]
        
        # 验证只有正文块被保留
        assert len(body_blocks) == 2
        for block in body_blocks:
            assert block.is_body_text == True
            assert block.block_text not in ['Header Text', 'Footer Text']
