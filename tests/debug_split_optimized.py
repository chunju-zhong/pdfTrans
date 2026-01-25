#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试优化后的翻译结果拆分逻辑
专门测试标点作为块首和单词拆分的情况
"""

from utils.text_processing import split_translated_result

# 测试1：英文单词不被拆分
def test_english_word_break():
    """测试英文单词不被拆分到两个块"""
    print("=== 测试1：英文单词不被拆分 ===")
    
    merged_translation = 'This is an English sentence with important words like artificial intelligence and machine learning.'
    original_blocks = [
        {'block_text': 'First part'},  # 较短的块
        {'block_text': 'Second part with more content'},  # 较长的块
        {'block_text': 'Final part'}  # 较短的块
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
    
    # 检查是否有单词被拆分
    for i in range(len(translated_blocks) - 1):
        current = translated_blocks[i]
        next_block = translated_blocks[i+1]
        if current and next_block:
            last_char = current[-1]
            first_char_next = next_block[0]
            if last_char.isalpha() and first_char_next.isalpha():
                print(f"\n注意：块 {i+1} 末尾 '{last_char}' 和块 {i+2} 开头 '{first_char_next}' 都是字母")
                print(f"块 {i+1}: '{current}'")
                print(f"块 {i+2}: '{next_block}'")

# 测试2：标点不作为块首
def test_punctuation_at_start():
    """测试块首没有标点符号"""
    print("\n\n=== 测试2：标点不作为块首 ===")
    
    merged_translation = '这是一个句子，包含标点符号。这是另一个句子，后面跟着标点符号！这是最后一个句子。'
    original_blocks = [
        {'block_text': 'Short block 1'},  # 较短的块
        {'block_text': 'Medium block with some content'},  # 中等长度的块
        {'block_text': 'Long block with more content that should get more translation text'},  # 较长的块
        {'block_text': 'Short block 2'}  # 较短的块
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
        if block and (block[0] in '.,;:?!。，、；：？！'):
            print(f"  ❌ 块首是标点符号: '{block[0]}'")
        else:
            print(f"  ✅ 块首不是标点符号")

# 测试3：中英文混合情况
def test_mixed_language():
    """测试中英文混合情况下的拆分"""
    print("\n\n=== 测试3：中英文混合情况 ===")
    
    merged_translation = 'This is English text with 中文内容 mixed together. 这是另一个中英文混合的句子，包含English words。'
    original_blocks = [
        {'block_text': 'First block'},  # 较短的块
        {'block_text': 'Second block with more content'},  # 中等长度的块
        {'block_text': 'Third block with the most content of all blocks'}  # 较长的块
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
        if block and (block[0] in '.,;:?!。，、；：？！'):
            print(f"  ❌ 块首是标点符号: '{block[0]}'")
        else:
            print(f"  ✅ 块首不是标点符号")

if __name__ == "__main__":
    test_english_word_break()
    test_punctuation_at_start()
    test_mixed_language()