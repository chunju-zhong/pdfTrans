import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.glossary_extractor import create_glossary_extractor


def test_no_glossary_line_removal():
    """测试移除包含NO_GLOSSARY的行"""
    # 创建术语提取器
    extractor = create_glossary_extractor('aiping')
    
    # 测试1：测试_format_glossary方法处理包含NO_GLOSSARY的行
    print("=== 测试1：测试_format_glossary方法处理包含NO_GLOSSARY的行 ===")
    
    # 测试文本1：包含NO_GLOSSARY行的文本
    test_text1 = """
    AI agents: AI智能体
    Large Language Model (LLM): 大语言模型（LLM）
    **NO_GLOSSARY**: **NO_GLOSSARY**
    Agent: 智能体
    NO_GLOSSARY: NO_GLOSSARY
    paradigm: 范式
    """
    
    # 调用_format_glossary方法
    result1 = extractor._format_glossary(test_text1)
    print(f"处理后的结果: \n{result1}")
    print(f"处理后的行数: {len(result1.strip().split('\n')) if result1.strip() else 0}")
    
    # 检查结果中是否包含NO_GLOSSARY
    if 'NO_GLOSSARY' in result1:
        print("\n❌ 错误：结果中仍然包含NO_GLOSSARY")
    else:
        print("\n✅ 成功：结果中不包含NO_GLOSSARY")
    
    # 测试2：测试只包含NO_GLOSSARY行的文本
    print("\n=== 测试2：测试只包含NO_GLOSSARY行的文本 ===")
    test_text2 = """
    **NO_GLOSSARY**: **NO_GLOSSARY**
    NO_GLOSSARY: NO_GLOSSARY
    """
    
    result2 = extractor._format_glossary(test_text2)
    print(f"处理后的结果: '{result2}'")
    print(f"处理后的行数: {len(result2.strip().split('\n')) if result2.strip() else 0}")
    
    if result2.strip() == '':
        print("\n✅ 成功：只包含NO_GLOSSARY的文本返回空字符串")
    else:
        print("\n❌ 错误：只包含NO_GLOSSARY的文本没有返回空字符串")
    
    # 测试3：测试正常的术语文本
    print("\n=== 测试3：测试正常的术语文本 ===")
    test_text3 = """
    AI agents: AI智能体
    Large Language Model (LLM): 大语言模型（LLM）
    Agent: 智能体
    paradigm: 范式
    """
    
    result3 = extractor._format_glossary(test_text3)
    print(f"处理后的结果: \n{result3}")
    print(f"处理后的行数: {len(result3.strip().split('\n')) if result3.strip() else 0}")
    
    if result3.strip() == test_text3.strip():
        print("\n✅ 成功：正常术语文本处理正确")
    else:
        print("\n❌ 错误：正常术语文本处理错误")


def test_silicon_flow_no_glossary_removal():
    """测试硅基流动提取器的NO_GLOSSARY行移除"""
    # 创建硅基流动术语提取器
    extractor = create_glossary_extractor('silicon_flow')
    
    print("\n=== 测试硅基流动提取器的NO_GLOSSARY行移除 ===")
    
    # 测试文本：包含NO_GLOSSARY行的文本
    test_text = """
    AI agents: AI智能体
    **NO_GLOSSARY**: **NO_GLOSSARY**
    Agent: 智能体
    """
    
    result = extractor._format_glossary(test_text)
    print(f"处理后的结果: \n{result}")
    print(f"处理后的行数: {len(result.strip().split('\n')) if result.strip() else 0}")
    
    # 检查结果中是否包含NO_GLOSSARY
    if 'NO_GLOSSARY' in result:
        print("\n❌ 错误：结果中仍然包含NO_GLOSSARY")
    else:
        print("\n✅ 成功：结果中不包含NO_GLOSSARY")


if __name__ == "__main__":
    test_no_glossary_line_removal()
    test_silicon_flow_no_glossary_removal()
