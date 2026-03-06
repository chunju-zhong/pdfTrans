#!/usr/bin/env python3
"""
测试约定俗成词汇的处理效果
"""
import logging
from modules.glossary_extractor import create_glossary_extractor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 测试文本，包含AI、AI Agent等约定俗成词汇
test_text = """AI agents are autonomous problem-solving systems that use large language models (LLMs) to perform tasks. The AI Agent paradigm represents a shift from passive, discrete tasks to active, continuous problem-solving. ChatGPT and Gemini are examples of AI systems that can be used as AI Agents."""

# 测试aiping提取器
def test_aiping_extractor():
    """测试aiping术语提取器"""
    print("\n=== 测试aiping术语提取器 ===")
    extractor = create_glossary_extractor('aiping')
    
    # 测试英文到中文的术语提取
    result_en_zh = extractor.extract_glossary(test_text, 'English', 'Chinese', '技术文档')
    print("英文到中文术语提取结果:")
    print(result_en_zh)
    
    # 检查约定俗成词汇是否保持原样
    check_terms(result_en_zh)

# 检查约定俗成词汇是否保持原样
def check_terms(result):
    """检查约定俗成词汇是否保持原样"""
    print("\n=== 检查约定俗成词汇 ===")
    lines = result.split('\n')
    
    # 约定俗成词汇列表
    common_terms = ['AI', 'AI Agent', 'AI Agents', 'ChatGPT', 'Gemini']
    
    for term in common_terms:
        found = False
        for line in lines:
            if term in line:
                # 检查是否保持原样（没有翻译）
                if line.strip() == f"{term}: {term}":
                    print(f"✓ {term}: 保持原样")
                else:
                    print(f"✗ {term}: 被翻译了: {line}")
                found = True
                break
        if not found:
            print(f"? {term}: 未提取")

if __name__ == "__main__":
    test_aiping_extractor()
