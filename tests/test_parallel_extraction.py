#!/usr/bin/env python3
"""测试并行文本提取和术语提取的性能"""

import time
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.glossary_service import glossary_service


def test_code_quality():
    """测试代码质量"""
    print("开始测试代码质量...")
    
    # 测试1: 检查方法是否存在
    assert hasattr(glossary_service, '_extract_page_text'), "_extract_page_text方法不存在"
    assert hasattr(glossary_service, 'extract_glossary_from_pdf'), "extract_glossary_from_pdf方法不存在"
    print("✓ 所有必要的方法都存在")
    
    # 测试2: 检查方法参数
    import inspect
    extractor_signature = inspect.signature(glossary_service.extract_glossary_from_pdf)
    assert 'pages' in extractor_signature.parameters, "extract_glossary_from_pdf方法缺少pages参数"
    assert 'task' in extractor_signature.parameters, "extract_glossary_from_pdf方法缺少task参数"
    print("✓ 方法参数完整")
    
    # 测试3: 检查_extract_page_text方法
    page_extractor_signature = inspect.signature(glossary_service._extract_page_text)
    assert 'pdf_path' in page_extractor_signature.parameters, "_extract_page_text方法缺少pdf_path参数"
    assert 'page_num' in page_extractor_signature.parameters, "_extract_page_text方法缺少page_num参数"
    print("✓ _extract_page_text方法参数完整")
    
    print("✓ 代码质量测试通过！")


def test_parallel_extraction():
    """测试并行文本提取和术语提取的性能"""
    # 测试文件路径（请替换为实际的PDF文件路径）
    test_pdf_path = "tests/test_files/sample.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"测试文件不存在: {test_pdf_path}")
        print("跳过性能测试，仅进行代码质量测试")
        test_code_quality()
        return
    
    print("开始测试并行文本提取和术语提取...")
    
    # 测试参数
    source_lang = "en"
    target_lang = "zh"
    extractor_type = "aiping"
    
    # 测试1: 并行处理所有页面
    print("\n测试1: 并行处理所有页面")
    start_time = time.time()
    glossary = glossary_service.extract_glossary_from_pdf(
        test_pdf_path, source_lang, target_lang, extractor_type
    )
    end_time = time.time()
    print(f"处理时间: {end_time - start_time:.2f} 秒")
    print(f"提取到的术语数: {len(glossary.split('\n')) if glossary else 0}")
    print(f"术语表预览: {glossary[:500]}..." if glossary else "未提取到术语")
    
    # 测试2: 并行处理指定页面
    print("\n测试2: 并行处理指定页面")
    pages = [1, 2, 3]
    start_time = time.time()
    glossary = glossary_service.extract_glossary_from_pdf(
        test_pdf_path, source_lang, target_lang, extractor_type, pages
    )
    end_time = time.time()
    print(f"处理时间: {end_time - start_time:.2f} 秒")
    print(f"提取到的术语数: {len(glossary.split('\n')) if glossary else 0}")
    print(f"术语表预览: {glossary[:500]}..." if glossary else "未提取到术语")
    
    print("\n测试完成！")


if __name__ == "__main__":
    test_parallel_extraction()

