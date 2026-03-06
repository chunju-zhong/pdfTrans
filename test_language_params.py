#!/usr/bin/env python3
"""
测试语言参数对术语提取的影响
"""
import logging
from modules.glossary_extractor import create_glossary_extractor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 测试文本（英文）
test_text = "Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data. Supervised learning and unsupervised learning are two main types of machine learning."

# 测试aiping提取器
def test_aiping_extractor():
    """测试aiping术语提取器"""
    print("\n=== 测试aiping术语提取器 ===")
    extractor = create_glossary_extractor('aiping')
    
    # 测试1: 使用语言代码
    print("\n测试1: 使用语言代码")
    result_code = extractor.extract_glossary(test_text, 'en', 'zh', '技术文档')
    print("英文到中文术语提取结果:")
    print(result_code)
    
    # 测试2: 使用语言名称
    print("\n测试2: 使用语言名称")
    result_name = extractor.extract_glossary(test_text, 'English', 'Chinese', '技术文档')
    print("英文到中文术语提取结果:")
    print(result_name)

if __name__ == "__main__":
    test_aiping_extractor()
