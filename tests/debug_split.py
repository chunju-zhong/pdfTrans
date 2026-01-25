#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试语义块拆分功能
"""

from utils.text_processing import split_translated_result

# 模拟实际的翻译场景
def debug_split_translation():
    """调试翻译结果拆分"""
    print("=== 调试翻译结果拆分 ===")
    
    # 场景1: 合并块包含多个句子，需要拆分到多个原始块
    print("\n场景1: 合并块包含多个句子，需要拆分到多个原始块")
    merged_translation = "人工智能正在发生变化。多年来，重点一直放在擅长被动、离散任务的模型上：回答问题、翻译文本或根据提示生成图像。这种范式虽然强大，但每一步都需要人类的持续指导。"
    original_blocks = [
        {'block_text': 'Artificial intelligence is changing. For years, the focus has been on models that excel at'},  # 长块
        {'block_text': 'passive, discrete tasks: answering a question, translating text, or generating an image from'},  # 长块  
        {'block_text': 'a prompt. This paradigm, while powerful, requires constant human direction for every step.'}  # 长块
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    print(f"原始块总长度: {sum(len(block['block_text']) for block in original_blocks)}")
    print(f"翻译文本长度: {len(merged_translation)}")
    
    for i, block in enumerate(original_blocks):
        print(f"原始块 {i+1}: '{block['block_text']}' (长度: {len(block['block_text'])})")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
    
    print(f"\n拆分结果总长度: {sum(len(block) for block in translated_blocks)}")
    
    # 场景2: 合并块只有一个句子，对应多个原始块
    print("\n\n场景2: 合并块只有一个句子，对应多个原始块")
    merged_translation = "智能体是语言模型的自然演进，在软件中变得有用。"
    original_blocks = [
        {'block_text': 'Agents are the natural evolution'},  # 短块
        {'block_text': 'of Language Models, made useful'},  # 短块
        {'block_text': 'in software.'}  # 短块
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    print(f"原始块总长度: {sum(len(block['block_text']) for block in original_blocks)}")
    print(f"翻译文本长度: {len(merged_translation)}")
    
    for i, block in enumerate(original_blocks):
        print(f"原始块 {i+1}: '{block['block_text']}' (长度: {len(block['block_text'])})")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
    
    print(f"\n拆分结果总长度: {sum(len(block) for block in translated_blocks)}")
    
    # 场景3: 原始块长度差异很大
    print("\n\n场景3: 原始块长度差异很大")
    merged_translation = "这是一个很长的句子，包含了很多内容，需要被拆分成多个块，其中一些块很短，一些块很长。"
    original_blocks = [
        {'block_text': 'Short block'},  # 短块
        {'block_text': 'This is a very long block that contains a lot of text and should be allocated more of the translation result.'},  # 长块
        {'block_text': 'Another short block'}  # 短块
    ]
    
    print(f"原始翻译文本: {merged_translation}")
    print(f"原始块数量: {len(original_blocks)}")
    print(f"原始块总长度: {sum(len(block['block_text']) for block in original_blocks)}")
    print(f"翻译文本长度: {len(merged_translation)}")
    
    for i, block in enumerate(original_blocks):
        print(f"原始块 {i+1}: '{block['block_text']}' (长度: {len(block['block_text'])})")
    
    translated_blocks = split_translated_result(merged_translation, original_blocks)
    
    print(f"\n拆分结果:")
    for i, block in enumerate(translated_blocks):
        print(f"拆分块 {i+1}: '{block}' (长度: {len(block)})")
    
    print(f"\n拆分结果总长度: {sum(len(block) for block in translated_blocks)}")

if __name__ == "__main__":
    debug_split_translation()