#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试文本溢出场景下的拆分逻辑
"""

from utils.text_processing import split_translated_result

# 模拟用户日志中的文本溢出场景
def debug_overflow_scenario():
    """调试文本溢出场景下的拆分逻辑"""
    print("=== 调试文本溢出场景下的拆分逻辑 ===")
    
    # 模拟用户日志中的文本
    user_log_text = "而无需复杂的账户或订阅机制。这两项协议共同构建了智能体网络的基础信任层。"
    print(f"用户日志中的文本: '{user_log_text}' (共 {len(user_log_text)} 字符)")
    
    # 模拟不同的原始块数量，测试拆分效果
    for num_blocks in [2, 3, 4]:
        print(f"\n场景: 拆分为 {num_blocks} 个原始块")
        
        # 创建模拟的原始块列表
        original_blocks = [{'block_text': f'Original block {i+1}'} for i in range(num_blocks)]
        
        print(f"原始翻译文本: {user_log_text}")
        print(f"原始块数量: {num_blocks}")
        print(f"翻译文本长度: {len(user_log_text)}")
        
        # 执行拆分
        translated_blocks = split_translated_result(user_log_text, original_blocks)
        
        print(f"\n拆分结果:")
        total_len = 0
        for i, block in enumerate(translated_blocks):
            block_len = len(block)
            total_len += block_len
            print(f"拆分块 {i+1}: '{block}' (长度: {block_len})")
            # 检查块首是否为标点
            if block and block[0] in '.,;:?!"\'()[]{}<>|/\\-_=+@#$%^&*。，、；：？！“”‘’`~（）【】{}《》|/＼－＿＝＋＠＃＄％＾＆＊':
                print(f"  ❌ 警告: 块首包含标点符号 '{block[0]}'")
            else:
                print(f"  ✅ 块首不是标点符号")
        
        print(f"\n拆分结果总长度: {total_len}")
        print(f"拆分结果平均长度: {total_len / num_blocks:.1f}")

# 测试长文本拆分，模拟PDF生成中的溢出场景
def debug_long_text_split():
    """调试长文本拆分"""
    print("\n\n=== 调试长文本拆分 ===")
    
    # 更长的测试文本，模拟PDF生成中的长句子
    long_text = "这是一个非常长的句子，用于测试PDF生成中的文本溢出问题。在实际应用中，当文本块的长度超过PDF页面的可用空间时，就会出现文本溢出。优化拆分逻辑可以确保每个文本块都能充分利用可用空间，同时保持良好的可读性。这需要考虑英文单词的完整性、标点符号的正确位置以及每个块的均匀分配。"
    print(f"测试长文本: '{long_text}' (共 {len(long_text)} 字符)")
    
    # 模拟拆分为多个块
    num_blocks = 5
    original_blocks = [{'block_text': f'Original block {i+1}'} for i in range(num_blocks)]
    
    print(f"\n拆分为 {num_blocks} 个块:")
    translated_blocks = split_translated_result(long_text, original_blocks)
    
    total_len = 0
    for i, block in enumerate(translated_blocks):
        block_len = len(block)
        total_len += block_len
        print(f"拆分块 {i+1}: '{block}' (长度: {block_len})")
        # 检查块首是否为标点
        if block and block[0] in '.,;:?!"\'()[]{}<>|/\\-_=+@#$%^&*。，、；：？！“”‘’`~（）【】{}《》|/＼－＿＝＋＠＃＄％＾＆＊':
            print(f"  ❌ 警告: 块首包含标点符号 '{block[0]}'")
        else:
            print(f"  ✅ 块首不是标点符号")
    
    print(f"\n拆分结果总长度: {total_len}")
    print(f"拆分结果平均长度: {total_len / num_blocks:.1f}")

if __name__ == "__main__":
    debug_overflow_scenario()
    debug_long_text_split()
