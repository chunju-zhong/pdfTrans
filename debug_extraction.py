#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本，用于分析页眉页脚识别逻辑问题
"""

import os
import sys
from modules.pdf_extractor import pdf_extractor

def debug_pdf_extraction():
    """调试PDF文本提取功能，分析页眉页脚识别问题"""
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
    
    print(f"开始调试PDF提取: {pdf_path}")
    
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
            
            # 计算页面尺寸
            all_bboxes = [block.block_bbox for block in page.text_blocks]
            min_y = min(bbox[1] for bbox in all_bboxes)
            max_y = max(bbox[3] for bbox in all_bboxes)
            page_height = max_y - min_y
            
            print(f"  页面尺寸（从文本块计算）:")
            print(f"    最小Y坐标: {min_y}")
            print(f"    最大Y坐标: {max_y}")
            print(f"    页面高度: {page_height}")
            
            # 计算页眉页脚阈值（15%）
            header_threshold = page_height * 0.15
            footer_threshold = page_height * (1 - 0.15)
            
            print(f"  页眉页脚阈值:")
            print(f"    页眉阈值（顶部15%）: {header_threshold}")
            print(f"    页脚阈值（底部15%）: {footer_threshold}")
            
            # 遍历文本块，显示详细信息
            for i, block in enumerate(page.text_blocks):
                bbox = block.block_bbox
                block_center_y = (bbox[1] + bbox[3]) / 2
                is_in_header = block_center_y <= header_threshold
                is_in_footer = block_center_y >= footer_threshold
                
                print(f"  块 {i+1}:")
                print(f"    文本: '{block.block_text}'")
                print(f"    位置: {block.block_bbox}")
                print(f"    中心Y坐标: {block_center_y}")
                print(f"    是否在页眉区域: {is_in_header}")
                print(f"    是否在页脚区域: {is_in_footer}")
                print(f"    是否为正文: {block.is_body_text}")
        
        # 分析页眉页脚识别逻辑
        print(f"\n页眉页脚识别分析:")
        print(f"- 页面数量: {result.total_pages}")
        print(f"- 页眉区域阈值: 页面高度的15%")
        print(f"- 页脚区域阈值: 页面高度的85%")
        print(f"- 出现频率阈值: 超过50%的页面")
        
        # 统计每个文本块在所有页面的出现次数
        text_counts = {}
        for page in result.pages:
            for block in page.text_blocks:
                text = block.block_text
                if text not in text_counts:
                    text_counts[text] = 0
                text_counts[text] += 1
        
        print(f"\n文本块出现频率:")
        for text, count in sorted(text_counts.items(), key=lambda x: x[1], reverse=True):
            frequency = count / result.total_pages * 100
            print(f"  '{text}': {count}次 ({frequency:.1f}%)")
        
        print("\n调试完成")
        return True
        
    except Exception as e:
        print(f"\n调试失败，错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_pdf_extraction()