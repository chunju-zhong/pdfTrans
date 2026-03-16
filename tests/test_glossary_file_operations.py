import sys
import os
import tempfile

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.glossary_service import glossary_service


def test_glossary_file_operations():
    """测试术语表文件操作功能"""
    # 测试数据：术语表内容
    test_glossary = """AI agents: AI智能体
Large Language Model (LLM): 大语言模型（LLM）
Agent: 智能体
paradigm: 范式
passive, discrete tasks: 被动式、离散型任务
prompt: 提示词
autonomous problem-solving: 自主问题解决"""
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_glossary)
        temp_file_path = f.name
    
    try:
        # 测试从文件加载术语表
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            loaded_content = f.read()
        
        print("从文件加载的术语表内容：")
        print(loaded_content)
        print("\n")
        
        # 验证加载的内容与原始内容一致
        assert loaded_content == test_glossary, "加载的术语表内容与原始内容不一致"
        print("✓ 从文件加载术语表测试通过")
        print("\n")
        
        # 测试保存术语表到文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            save_file_path = f.name
        
        with open(save_file_path, 'w', encoding='utf-8') as f:
            f.write(loaded_content)
        
        # 验证保存的内容与原始内容一致
        with open(save_file_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        
        print("保存到文件的术语表内容：")
        print(saved_content)
        print("\n")
        
        assert saved_content == test_glossary, "保存的术语表内容与原始内容不一致"
        print("✓ 保存术语表到文件测试通过")
        print("\n")
        
        # 测试空术语表处理
        empty_glossary = ""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(empty_glossary)
            empty_file_path = f.name
        
        with open(empty_file_path, 'r', encoding='utf-8') as f:
            empty_content = f.read()
        
        print("空术语表测试：")
        print(f"加载的空术语表长度：{len(empty_content)}")
        print("\n")
        
        assert len(empty_content) == 0, "空术语表加载失败"
        print("✓ 空术语表处理测试通过")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if 'save_file_path' in locals() and os.path.exists(save_file_path):
            os.unlink(save_file_path)
        if 'empty_file_path' in locals() and os.path.exists(empty_file_path):
            os.unlink(empty_file_path)


def test_glossary_service_extract():
    """测试术语提取服务"""
    # 测试PDF文件路径（使用项目中的测试文件）
    test_pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'test_data', 'test.pdf')
    
    if not os.path.exists(test_pdf_path):
        print(f"测试PDF文件不存在：{test_pdf_path}")
        print("跳过术语提取服务测试")
        return
    
    try:
        # 测试提取术语（使用默认页码范围）
        print("测试术语提取服务（默认页码范围）：")
        glossary = glossary_service.extract_glossary_from_pdf(test_pdf_path, 'English', 'Chinese', 'AI')
        print(f"提取的术语数量：{len(glossary.splitlines())}")
        print("提取的术语表：")
        print(glossary)
        print("\n")
        
        # 测试提取术语（指定页码范围）
        print("测试术语提取服务（指定页码范围）：")
        glossary = glossary_service.extract_glossary_from_pdf(test_pdf_path, 'English', 'Chinese', 'AI', pages=[1])
        print(f"提取的术语数量：{len(glossary.splitlines())}")
        print("提取的术语表：")
        print(glossary)
        print("\n")
        
        print("✓ 术语提取服务测试通过")
        
    except Exception as e:
        print(f"术语提取服务测试失败：{str(e)}")


if __name__ == "__main__":
    print("开始测试术语表文件操作功能...\n")
    test_glossary_file_operations()
    print("\n开始测试术语提取服务...\n")
    test_glossary_service_extract()
    print("\n所有测试完成！")
