#!/usr/bin/env python3
"""
测试只提取源语言中的专业术语
"""
import logging
from modules.glossary_extractor import create_glossary_extractor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 测试文本（包含中英文术语）
test_text = "Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data. 监督学习和无监督学习是机器学习的两种主要类型。"

# 测试aiping提取器
def test_aiping_extractor():
    """测试aiping术语提取器"""
    print("\n=== 测试aiping术语提取器 ===")
    extractor = create_glossary_extractor('aiping')
    
    # 测试英文到中文的术语提取（源语言为英文）
    print("\n测试1: 英文到中文术语提取（源语言为英文）")
    result_en_zh = extractor.extract_glossary(test_text, 'English', 'Chinese', '技术文档')
    print("英文到中文术语提取结果:")
    print(result_en_zh)
    
    # 测试中文到英文的术语提取（源语言为中文）
    print("\n测试2: 中文到英文术语提取（源语言为中文）")
    result_zh_en = extractor.extract_glossary(test_text, 'Chinese', 'English', '技术文档')
    print("中文到英文术语提取结果:")
    print(result_zh_en)

if __name__ == "__main__":
    test_aiping_extractor()
