import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.glossary_extractor import create_glossary_extractor


def test_no_glossary_handling():
    """测试术语提取器在没有专业术语时返回空字符串"""
    # 创建术语提取器
    extractor = create_glossary_extractor('aiping')
    
    # 测试1：无专业术语的文本
    test_text1 = """
    今天天气很好，我去公园散步。公园里有很多人，大家都在享受美好的时光。
    我看到了一些花，还有一些树。阳光很温暖，微风拂面，感觉非常舒服。
    """
    
    print("=== 测试1：无专业术语的文本 ===")
    glossary1 = extractor.extract_glossary(test_text1, 'Chinese', 'English', 'AI')
    print(f"提取结果: '{glossary1}'")
    print(f"提取结果长度: {len(glossary1)}")
    print(f"是否为空字符串: {glossary1 == ''}")
    print("\n")
    
    # 测试2：只有普通词汇的文本
    test_text2 = """
    我喜欢使用电脑，每天都会上网。有时候会看电影，有时候会听音乐。
    我还喜欢读书，尤其是小说和散文。周末的时候，我会和朋友一起出去吃饭。
    """
    
    print("=== 测试2：只有普通词汇的文本 ===")
    glossary2 = extractor.extract_glossary(test_text2, 'Chinese', 'English', 'AI')
    print(f"提取结果: '{glossary2}'")
    print(f"提取结果长度: {len(glossary2)}")
    print(f"是否为空字符串: {glossary2 == ''}")
    print("\n")
    
    # 测试3：有专业术语的文本
    test_text3 = """
    人工智能技术在近年来得到了快速发展。机器学习和深度学习成为了热门话题。
    神经网络和自然语言处理技术也在不断进步。
    """
    
    print("=== 测试3：有专业术语的文本 ===")
    glossary3 = extractor.extract_glossary(test_text3, 'Chinese', 'English', 'AI')
    print(f"提取结果: '{glossary3}'")
    print(f"提取结果长度: {len(glossary3)}")
    print(f"是否为空字符串: {glossary3 == ''}")
    print("\n")
    
    # 测试4：直接测试NO_GLOSSARY标识处理
    print("=== 测试4：直接测试NO_GLOSSARY标识处理 ===")
    # 测试Aiping提取器的_format_glossary方法
    aiping_extractor = create_glossary_extractor('aiping')
    result1 = aiping_extractor._format_glossary('NO_GLOSSARY')
    print(f"Aiping提取器处理'NO_GLOSSARY'结果: '{result1}'")
    print(f"结果是否为空字符串: {result1 == ''}")
    
    # 测试SiliconFlow提取器的_format_glossary方法
    silicon_flow_extractor = create_glossary_extractor('silicon_flow')
    result2 = silicon_flow_extractor._format_glossary('NO_GLOSSARY')
    print(f"SiliconFlow提取器处理'NO_GLOSSARY'结果: '{result2}'")
    print(f"结果是否为空字符串: {result2 == ''}")
    print("\n")
    
    # 测试5：测试正常术语处理
    print("=== 测试5：测试正常术语处理 ===")
    test_terms = """
    人工智能: Artificial Intelligence
    机器学习: Machine Learning
    深度学习: Deep Learning
    """
    result3 = aiping_extractor._format_glossary(test_terms)
    print(f"Aiping提取器处理正常术语结果: '{result3}'")
    print(f"结果是否为空字符串: {result3 == ''}")


if __name__ == "__main__":
    test_no_glossary_handling()
