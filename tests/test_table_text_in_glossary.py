import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.glossary_service import glossary_service


def test_table_text_extraction_logic():
    """测试表格文本提取逻辑"""
    from models.extraction import PdfTable
    
    print("=== 测试表格文本提取逻辑 ===")
    
    # 创建一个模拟的表格对象
    mock_table = PdfTable(
        page_num=1,
        table_idx=0,
        bbox=(0, 0, 100, 100),
        cells=[
            ["术语", "解释"],
            ["机器学习", "一种人工智能技术"],
            ["深度学习", "机器学习的一个分支"],
            ["神经网络", "模仿人脑结构的计算模型"]
        ]
    )
    
    # 测试_extract_text_from_table方法
    table_text = glossary_service._extract_text_from_table(mock_table)
    print(f"提取的表格文本: \n{table_text}")
    
    # 验证表格文本提取结果
    expected_text = "术语 | 解释\n机器学习 | 一种人工智能技术\n深度学习 | 机器学习的一个分支\n神经网络 | 模仿人脑结构的计算模型\n"
    if table_text == expected_text:
        print("\n表格文本提取逻辑测试通过")
    else:
        print("\n表格文本提取逻辑测试失败")
        print(f"期望结果: \n{expected_text}")


def test_glossary_service_import():
    """测试术语提取服务导入"""
    print("\n=== 测试术语提取服务导入 ===")
    try:
        from services.glossary_service import glossary_service
        print("术语提取服务导入成功")
        print(f"服务类型: {type(glossary_service)}")
        return True
    except Exception as e:
        print(f"术语提取服务导入失败: {str(e)}")
        return False


def test_method_exists():
    """测试方法是否存在"""
    print("\n=== 测试方法是否存在 ===")
    from services.glossary_service import glossary_service
    
    # 检查_extract_text_from_table方法是否存在
    if hasattr(glossary_service, '_extract_text_from_table'):
        print("_extract_text_from_table方法存在")
    else:
        print("_extract_text_from_table方法不存在")
    
    # 检查_extract_text_from_pdf方法是否存在
    if hasattr(glossary_service, '_extract_text_from_pdf'):
        print("_extract_text_from_pdf方法存在")
    else:
        print("_extract_text_from_pdf方法不存在")
    
    # 检查_extract_page_text方法是否存在
    if hasattr(glossary_service, '_extract_page_text'):
        print("_extract_page_text方法存在")
    else:
        print("_extract_page_text方法不存在")


if __name__ == "__main__":
    test_glossary_service_import()
    test_method_exists()
    test_table_text_extraction_logic()
