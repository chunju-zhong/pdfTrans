#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查现有测试数据文件的内容和结构
"""

import fitz
import os

# 检查现有测试数据文件
tests_dir = "/Users/chunju/work/pdfTrans/tests/data"

existing_files = [f for f in os.listdir(tests_dir) if f.endswith('.pdf')]

print(f"现有测试数据文件: {existing_files}")

# 分析每个文件
for file_name in existing_files:
    file_path = os.path.join(tests_dir, file_name)
    print(f"\n=== 分析文件: {file_name} ===")
    
    with fitz.open(file_path) as doc:
        print(f"页数: {len(doc)}")
        
        # 查看第一页内容
        if len(doc) > 0:
            page = doc[0]
            text = page.get_text()
            print(f"第一页文本长度: {len(text)} 字符")
            print(f"第一页前100字符: {text[:100]}...")
            
            # 检查是否包含表格
            if "table" in file_name.lower():
                print("文件名称包含'table'，可能包含表格")
            
            # 检查是否包含图片
            if "img" in file_name.lower():
                print("文件名称包含'img'，可能包含图片")
                images = page.get_images(full=True)
                print(f"第一页图片数量: {len(images)}")

# 检查是否有其他测试数据文件可用
print("\n=== 检查其他位置的测试数据文件 ===")
tmp_dir = "/Users/chunju/work/pdfTrans/tests/tmp"
tmp_files = [f for f in os.listdir(tmp_dir) if f.endswith('.pdf') and 'test_data' in f]
print(f"/tests/tmp/目录中的测试数据文件: {tmp_files}")

# 检查outputs目录中的翻译结果文件
outputs_dir = "/Users/chunju/work/pdfTrans/outputs"
output_files = [f for f in os.listdir(outputs_dir) if f.endswith('.pdf') and 'test_data' in f]
print(f"/outputs/目录中的翻译结果文件数量: {len(output_files)}")
if output_files:
    print(f"前5个翻译结果文件: {output_files[:5]}")
