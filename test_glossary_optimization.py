#!/usr/bin/env python3
"""
测试术语提取优化
"""
import logging
from modules.glossary_extractor import create_glossary_extractor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 测试文本
test_text = """AI agents are autonomous problem-solving systems that use large language models (LLMs) to perform tasks. The agent paradigm represents a shift from passive, discrete tasks to active, continuous problem-solving."""

# 测试aiping提取器
def test_aiping_extractor():
    """测试aiping术语提取器"""
    print("\n=== 测试aiping术语提取器 ===")
    extractor = create_glossary_extractor('aiping')
    
    # 测试英文到中文的术语提取
    result_en_zh = extractor.extract_glossary(test_text, 'English', 'Chinese', '技术文档')
    print("英文到中文术语提取结果:")
    print(result_en_zh)
    
    # 测试英文到英文的术语提取（应该不提供翻译）
    result_en_en = extractor.extract_glossary(test_text, 'English', 'English', '技术文档')
    print("\n英文到英文术语提取结果:")
    print(result_en_en)

# 测试硅基流动提取器
def test_silicon_flow_extractor():
    """测试硅基流动术语提取器"""
    print("\n=== 测试硅基流动术语提取器 ===")
    extractor = create_glossary_extractor('silicon_flow')
    
    # 测试英文到中文的术语提取
    result_en_zh = extractor.extract_glossary(test_text, 'English', 'Chinese', '技术文档')
    print("英文到中文术语提取结果:")
    print(result_en_zh)
    
    # 测试英文到英文的术语提取（应该不提供翻译）
    result_en_en = extractor.extract_glossary(test_text, 'English', 'English', '技术文档')
    print("\n英文到英文术语提取结果:")
    print(result_en_en)

if __name__ == "__main__":
    test_aiping_extractor()
    test_silicon_flow_extractor()
