# -*- coding: utf-8 -*-
"""
语义合并测试
"""

import pytest
from utils.text_processing import merge_semantic_blocks, split_translated_result
from models.text_block import TextBlock

class TestSemanticMerge:
    """语义合并测试类"""
    
    def test_merge_semantic_blocks(self):
        """测试语义块合并功能
        
        验证merge_semantic_blocks方法能够正确合并语义相关的文本块
        """
        # 创建测试用的TextBlock对象
        text_blocks = [
            TextBlock(block_no=1, text="这是第一行文本。", bbox=(0, 0, 100, 20)),
            TextBlock(block_no=2, text="这是第二行文本。", bbox=(0, 20, 100, 40)),
            TextBlock(block_no=3, text="这是第三行文本。", bbox=(0, 40, 100, 60))
        ]
        
        # 调用语义合并方法，返回的是一个元组(merged_blocks, block_mapping)
        merged_blocks, block_mapping = merge_semantic_blocks(text_blocks)
        
        # 验证结果
        assert isinstance(merged_blocks, list)
        assert len(merged_blocks) > 0
        assert isinstance(block_mapping, list)
    
    def test_split_translated_result(self):
        """测试翻译结果拆分功能
        
        验证split_translated_result方法能够正确拆分翻译后的文本结果
        """
        # 创建测试用的TextBlock对象
        original_blocks = [
            TextBlock(block_no=1, text="第一句。", bbox=(0, 0, 100, 20)),
            TextBlock(block_no=2, text="第二句。", bbox=(0, 20, 100, 40)),
            TextBlock(block_no=3, text="第三句。", bbox=(0, 40, 100, 60))
        ]
        
        translated_text = "First sentence. Second sentence. Third sentence."
        
        # 调用拆分方法
        split_result = split_translated_result(original_blocks, translated_text)
        
        # 验证结果
        assert isinstance(split_result, list)
        assert len(split_result) == len(original_blocks)
    
    def test_split_translated_result_mismatch(self):
        """测试翻译结果与原文本不匹配的情况
        
        验证split_translated_result方法在翻译结果与原文本不匹配时能够正确处理
        """
        # 创建测试用的TextBlock对象
        original_blocks = [
            TextBlock(block_no=1, text="第一句。第二句。第三句。", bbox=(0, 0, 100, 20))
        ]
        
        translated_text = "First sentence. Second sentence. Third sentence."
        
        # 调用拆分方法
        split_result = split_translated_result(original_blocks, translated_text)
        
        # 验证结果
        assert isinstance(split_result, list)
        assert len(split_result) == len(original_blocks)
