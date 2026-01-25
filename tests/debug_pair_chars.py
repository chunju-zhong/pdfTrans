#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试成对字符处理逻辑
"""

from utils.text_processing import split_translated_result, is_left_pair_character

# 测试成对字符处理
def debug_pair_chars():
    """调试成对字符处理逻辑"""
    print("=== 调试成对字符处理逻辑 ===")
    
    # 场景1: 包含左引号的文本
    print("\n场景1: 包含左引号的文本")
    merged_translation = '"这是一个带有左引号的句子，应该被正确拆分。"这是另一个句子。'
    original_blocks = [
        {'block_text': 'This is a sentence with quotes.'},
        {'block_text': 'This is another sentence.'}
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    print(f"翻译文本长度: {len(merged_translation)}")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
        # 检查块尾是否为左成对字符
        if block and is_left_pair_character(block[-1]):
            print(f"  ❌ 警告: 块尾包含左成对字符 '{block[-1]}'")
        else:
            print(f"  ✅ 块尾不是左成对字符")
    
    # 场景2: 包含括号的文本
    print("\n\n场景2: 包含括号的文本")
    merged_translation = '这是一个带有(括号)的句子，应该被正确拆分。(这是另一个括号内的内容。)'
    original_blocks = [
        {'block_text': 'This is a sentence with parentheses.'},
        {'block_text': 'This is another sentence with parentheses.'}
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    print(f"翻译文本长度: {len(merged_translation)}")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
        # 检查块尾是否为左成对字符
        if block and is_left_pair_character(block[-1]):
            print(f"  ❌ 警告: 块尾包含左成对字符 '{block[-1]}'")
        else:
            print(f"  ✅ 块尾不是左成对字符")
    
    # 场景3: 包含书名号的文本
    print("\n\n场景3: 包含书名号的文本")
    merged_translation = '这是《书名号》内的内容，应该被正确拆分。《这是另一本书》的内容。'
    original_blocks = [
        {'block_text': 'This is content inside书名号.'},
        {'block_text': 'This is content from another book.'}
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    print(f"翻译文本长度: {len(merged_translation)}")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
        # 检查块尾是否为左成对字符
        if block and is_left_pair_character(block[-1]):
            print(f"  ❌ 警告: 块尾包含左成对字符 '{block[-1]}'")
        else:
            print(f"  ✅ 块尾不是左成对字符")
    
    # 场景4: 包含多种成对字符的文本
    print("\n\n场景4: 包含多种成对字符的文本")
    merged_translation = '这是"引号"和(括号)以及《书名号》的混合使用，应该被正确拆分。"这是另一个引号"(包含括号)《和书名号》。'
    original_blocks = [
        {'block_text': 'This is a mix of quotes, parentheses, and书名号.'},
        {'block_text': 'This is another mix of different pair characters.'},
        {'block_text': 'This is the final sentence.'}
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    print(f"翻译文本长度: {len(merged_translation)}")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
        # 检查块尾是否为左成对字符
        if block and is_left_pair_character(block[-1]):
            print(f"  ❌ 警告: 块尾包含左成对字符 '{block[-1]}'")
        else:
            print(f"  ✅ 块尾不是左成对字符")

if __name__ == "__main__":
    debug_pair_chars()
