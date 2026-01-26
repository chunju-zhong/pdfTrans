#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试脚本，用于分析页眉页脚识别逻辑问题
"""

import os
import sys
import fitz  # PyMuPDF
from modules.pdf_extractor import pdf_extractor

def debug_pdf_detailed():
    """详细调试PDF文本提取功能，分析页眉页脚识别问题"""
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
    
    print(f"开始详细调试PDF提取: {pdf_path}")
    
    # 首先直接使用PyMuPDF查看页面信息
    with fitz.open(pdf_path) as doc:
        print(f"\nPDF基本信息:")
        print(f"  总页数: {len(doc)}")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_rect = page.rect
            print(f"\n页面 {page_num + 1}:")
            print(f"  页面尺寸: {page_rect}")
            print(f"  页面宽度: {page_rect.width}")
            print(f"  页面高度: {page_rect.height}")
            print(f"  页面左下角: {page_rect.bottom_left}")
            print(f"  页面右下角: {page_rect.bottom_right}")
            print(f"  页面左上角: {page_rect.top_left}")
            print(f"  页面右上角: {page_rect.top_right}")
            
            # 提取文本块
            blocks = page.get_text("blocks", flags=1)
            print(f"  文本块数量: {len(blocks)}")
            
            # 打印每个文本块的详细信息
            for i, block in enumerate(blocks):
                x0, y0, x1, y1, text, block_no, block_type = block
                if block_type == 0 and text.strip():
                    print(f"  块 {i+1}:")
                    print(f"    文本: '{text.strip()}'")
                    print(f"    位置: ({x0}, {y0}, {x1}, {y1})")
                    print(f"    宽度: {x1 - x0}")
                    print(f"    高度: {y1 - y0}")
                    print(f"    中心X: {(x0 + x1) / 2}")
                    print(f"    中心Y: {(y0 + y1) / 2}")
                    print(f"    块编号: {block_no}")
                    print(f"    块类型: {block_type}")
    
    # 然后使用我们的提取器提取文本
    print(f"\n\n使用自定义提取器提取文本:")
    try:
        result = pdf_extractor.extract_text(pdf_path)
        
        print(f"\n提取结果:")
        print(f"总页数: {result.total_pages}")
        print(f"表格数量: {len(result.tables)}")
        
        # 遍历所有页面
        for page in result.pages:
            print(f"\n页面 {page.page_num}:")
            print(f"  文本块数量: {len(page.text_blocks)}")
            
            # 遍历文本块，显示详细信息
            for i, block in enumerate(page.text_blocks):
                bbox = block.block_bbox
                block_center_y = (bbox[1] + bbox[3]) / 2
                
                print(f"  块 {i+1}:")
                print(f"    文本: '{block.block_text}'")
                print(f"    位置: {block.block_bbox}")
                print(f"    中心Y坐标: {block_center_y}")
                print(f"    是否为正文: {block.is_body_text}")
    except Exception as e:
        print(f"\n提取失败，错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n详细调试完成")

if __name__ == "__main__":
    debug_pdf_detailed()