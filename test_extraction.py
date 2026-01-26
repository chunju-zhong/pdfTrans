#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF提取功能验证脚本

用于验证PDF文本提取功能是否正常工作，以及is_body_text属性是否被正确添加和标记。
"""

import os
import sys
from modules.pdf_extractor import pdf_extractor

def test_pdf_extraction():
    """测试PDF文本提取功能"""
    # 检查是否提供了PDF文件路径
    if len(sys.argv) < 2:
        print("请提供PDF文件路径作为参数")
        print(f"用法: {sys.argv[0]} <pdf_file_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"PDF文件不存在: {pdf_path}")
        sys.exit(1)
    
    print(f"开始测试PDF提取: {pdf_path}")
    
    try:
        # 提取PDF文本
        result = pdf_extractor.extract_text(pdf_path)
        
        print(f"\n提取结果:")
        print(f"总页数: {result.total_pages}")
        print(f"表格数量: {len(result.tables)}")
        
        # 遍历所有页面
        for page in result.pages:
            print(f"\n页面 {page.page_num}:")
            print(f"  文本块数量: {len(page.text_blocks)}")
            
            # 遍历文本块，检查is_body_text属性
            for i, block in enumerate(page.text_blocks):
                print(f"  块 {i+1}:")
                print(f"    文本: '{block.block_text}'")
                print(f"    位置: {block.block_bbox}")
                print(f"    字体: {block.font}")
                print(f"    字号: {block.font_size}")
                print(f"    粗体: {block.bold}")
                print(f"    斜体: {block.italic}")
                print(f"    是否为正文: {block.is_body_text}")
        
        print("\n测试完成，PDF提取功能正常工作！")
        return True
        
    except Exception as e:
        print(f"\n测试失败，错误信息: {str(e)}")
        return False

if __name__ == "__main__":
    test_pdf_extraction()