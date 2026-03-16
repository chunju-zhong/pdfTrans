import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.glossary_extractor import create_glossary_extractor


def test_empty_glossary_extraction():
    """测试提取不到术语时返回空字符串"""
    # 创建术语提取器
    extractor = create_glossary_extractor('aiping')
    
    # 测试文本（没有专业术语）
    test_text = """
    今天天气很好，我去公园散步。公园里有很多人，大家都在享受美好的时光。
    我看到了一些花，还有一些树。阳光很温暖，微风拂面，感觉非常舒服。
    """
    
    print("=== 测试无专业术语的文本 ===")
    glossary = extractor.extract_glossary(test_text, 'Chinese', 'English', 'AI')
    print(f"提取结果: '{glossary}'")
    print(f"提取结果长度: {len(glossary)}")
    print(f"是否为空字符串: {glossary == ''}")
    print("\n")
    
    # 测试文本（有少量普通词汇，没有专业术语）
    test_text2 = """
    我喜欢使用电脑，每天都会上网。有时候会看电影，有时候会听音乐。
    我还喜欢读书，尤其是小说和散文。周末的时候，我会和朋友一起出去吃饭。
    """
    
    print("=== 测试只有普通词汇的文本 ===")
    glossary2 = extractor.extract_glossary(test_text2, 'Chinese', 'English', 'AI')
    print(f"提取结果: '{glossary2}'")
    print(f"提取结果长度: {len(glossary2)}")
    print(f"是否为空字符串: {glossary2 == ''}")
    print("\n")
    
    # 测试文本（有专业术语的文本，作为对比）
    test_text3 = """
    人工智能技术在近年来得到了快速发展。机器学习和深度学习成为了热门话题。
    神经网络和自然语言处理技术也在不断进步。
    """
    
    print("=== 测试有专业术语的文本 ===")
    glossary3 = extractor.extract_glossary(test_text3, 'Chinese', 'English', 'AI')
    print(f"提取结果: '{glossary3}'")
    print(f"提取结果长度: {len(glossary3)}")
    print(f"是否为空字符串: {glossary3 == ''}")


if __name__ == "__main__":
    test_empty_glossary_extraction()
