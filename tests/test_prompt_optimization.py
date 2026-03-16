import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.glossary_extractor import create_glossary_extractor


def test_prompt_optimization():
    """测试优化后的提示词是否能够避免模型返回中间结果"""
    # 创建术语提取器
    extractor = create_glossary_extractor('aiping')
    
    # 测试文本1：包含专业术语的文本
    test_text1 = """
    Data-centric AI is a paradigm that focuses on the quality and management of data. 
    It differs from model-centric AI, which focuses on improving model architecture and training techniques. 
    Deep learning models require high-quality datasets to achieve good performance on benchmarks.
    Andrew Ng has been a prominent advocate for data-centric AI approaches.
    """
    
    print("=== 测试1：包含专业术语的文本 ===")
    glossary1 = extractor.extract_glossary(test_text1, 'English', 'Chinese', 'AI')
    print(f"提取的术语表: \n{glossary1}")
    print(f"提取的术语数量: {len(glossary1.strip().split('\n')) if glossary1.strip() else 0}")
    
    # 检查是否包含中间结果或注释
    if '（注：' in glossary1 or '修正后输出：' in glossary1:
        print("\n❌ 错误：术语表中包含注释或中间结果")
    else:
        print("\n✅ 成功：术语表中不包含注释或中间结果")
    
    # 测试文本2：包含普通词汇的文本
    test_text2 = """
    Today is a beautiful day. I went to the park and saw many people. 
    The sun was shining, and the birds were singing. It was a perfect day for a walk.
    """
    
    print("\n=== 测试2：包含普通词汇的文本 ===")
    glossary2 = extractor.extract_glossary(test_text2, 'English', 'Chinese', 'AI')
    print(f"提取的术语表: '{glossary2}'")
    print(f"提取的术语数量: {len(glossary2.strip().split('\n')) if glossary2.strip() else 0}")
    
    # 检查是否包含中间结果或注释
    if '（注：' in glossary2 or '修正后输出：' in glossary2:
        print("\n❌ 错误：术语表中包含注释或中间结果")
    else:
        print("\n✅ 成功：术语表中不包含注释或中间结果")
    
    # 测试文本3：包含混合内容的文本
    test_text3 = """
    In the field of artificial intelligence, machine learning and deep learning are important concepts. 
    Machine learning algorithms are used to train models on large datasets. 
    Deep learning, a subset of machine learning, uses neural networks with multiple layers.
    John Smith is a researcher in this field.
    """
    
    print("\n=== 测试3：包含混合内容的文本 ===")
    glossary3 = extractor.extract_glossary(test_text3, 'English', 'Chinese', 'AI')
    print(f"提取的术语表: \n{glossary3}")
    print(f"提取的术语数量: {len(glossary3.strip().split('\n')) if glossary3.strip() else 0}")
    
    # 检查是否包含中间结果或注释
    if '（注：' in glossary3 or '修正后输出：' in glossary3:
        print("\n❌ 错误：术语表中包含注释或中间结果")
    else:
        print("\n✅ 成功：术语表中不包含注释或中间结果")


def test_silicon_flow_prompt():
    """测试硅基流动提取器的提示词优化"""
    # 创建硅基流动术语提取器
    extractor = create_glossary_extractor('silicon_flow')
    
    # 测试文本：包含专业术语的文本
    test_text = """
    Data-centric AI is a paradigm that focuses on the quality and management of data. 
    It differs from model-centric AI, which focuses on improving model architecture and training techniques. 
    Deep learning models require high-quality datasets to achieve good performance on benchmarks.
    """
    
    print("\n=== 测试硅基流动提取器 ===")
    glossary = extractor.extract_glossary(test_text, 'English', 'Chinese', 'AI')
    print(f"提取的术语表: \n{glossary}")
    print(f"提取的术语数量: {len(glossary.strip().split('\n')) if glossary.strip() else 0}")
    
    # 检查是否包含中间结果或注释
    if '（注：' in glossary or '修正后输出：' in glossary:
        print("\n❌ 错误：术语表中包含注释或中间结果")
    else:
        print("\n✅ 成功：术语表中不包含注释或中间结果")


if __name__ == "__main__":
    test_prompt_optimization()
    test_silicon_flow_prompt()
