import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.glossary_extractor import create_glossary_extractor


def test_glossary_extraction():
    """测试术语提取功能"""
    # 创建术语提取器
    extractor = create_glossary_extractor('aiping')
    
    # 测试文本（英文）
    test_text = """
    AI Agents are becoming increasingly popular in the field of artificial intelligence. They are designed to perform specific tasks autonomously. 
    Machine learning algorithms are used to train these agents. Natural language processing is another important technology in this domain.
    """
    
    # 提取术语（英文到中文）
    glossary = extractor.extract_glossary(test_text, 'English', 'Chinese', 'AI')
    print("提取的术语表：")
    print(glossary)
    print("\n")
    
    # 测试文本（中文）
    test_text_cn = """
    人工智能代理在人工智能领域变得越来越流行。它们被设计用来自主执行特定任务。
    机器学习算法被用来训练这些代理。自然语言处理是这个领域的另一项重要技术。
    """
    
    # 提取术语（中文到英文）
    glossary_cn = extractor.extract_glossary(test_text_cn, 'Chinese', 'English', 'AI')
    print("提取的术语表（中文到英文）：")
    print(glossary_cn)


if __name__ == "__main__":
    test_glossary_extraction()
