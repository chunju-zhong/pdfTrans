#!/usr/bin/env python3
"""
测试无术语情况的处理效果
"""
import logging
from modules.glossary_extractor import create_glossary_extractor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 普通文本（无专业术语）
plain_text = "今天天气很好，我去公园散步。路上遇到了一个朋友，我们聊了一会儿天。然后我回家吃了午饭，看了一会儿电视。"

# 包含专业术语的文本
technical_text = "AI agents are autonomous problem-solving systems that use large language models (LLMs) to perform tasks. The AI Agent paradigm represents a shift from passive, discrete tasks to active, continuous problem-solving."

# 测试aiping提取器
def test_aiping_extractor():
    """测试aiping术语提取器"""
    print("\n=== 测试aiping术语提取器 ===")
    extractor = create_glossary_extractor('aiping')
    
    # 测试普通文本（无专业术语）
    result_plain = extractor.extract_glossary(plain_text, 'Chinese', 'English', '日常对话')
    print("普通文本提取结果:")
    print(f"结果长度: {len(result_plain)}")
    print(f"结果内容: '{result_plain}'")
    
    # 测试包含专业术语的文本
    result_technical = extractor.extract_glossary(technical_text, 'English', 'Chinese', '技术文档')
    print("\n包含专业术语的文本提取结果:")
    print(result_technical)

if __name__ == "__main__":
    test_aiping_extractor()
