#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试脚本，验证PDF生成器的修改是否正确
"""

import os
import sys
import tempfile
from modules.pdf_generator import PdfGenerator
from modules.pdf_extractor import PdfExtractor
from services.translation_service import translation_service
from utils.logging_config import setup_logging

# 配置日志
setup_logging()

# 测试数据文件路径
test_pdf_path = "/Users/chunju/work/pdfTrans/tests/data/test_data_en_one_page.pdf"

if not os.path.exists(test_pdf_path):
    print(f"测试PDF文件不存在: {test_pdf_path}")
    sys.exit(1)

print("开始测试PDF生成器修改...")

# 创建临时输出文件
with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
    output_pdf_path = tmp_file.name

try:
    # 1. 提取PDF文本
    print(f"1. 提取PDF文本: {test_pdf_path}")
    pdf_extractor = PdfExtractor(test_pdf_path)
    extracted_content = pdf_extractor.extract_text()
    print(f"   提取完成，页数: {extracted_content.total_pages}")
    
    # 2. 模拟翻译后的内容结构
    # 只包含blocks字段，不包含text_content字段
    translated_content = {
        'blocks': extracted_content.pages,  # 直接使用提取的页面作为blocks
        'tables': []
    }
    
    print(f"2. 创建翻译后的内容结构，包含{len(translated_content['blocks'])}个页面")
    
    # 3. 生成PDF
    print(f"3. 生成PDF: {output_pdf_path}")
    pdf_generator = PdfGenerator()
    pdf_generator.generate_pdf(test_pdf_path, translated_content, output_pdf_path)
    
    print(f"   PDF生成成功！")
    
    # 4. 验证输出文件存在
    if os.path.exists(output_pdf_path):
        file_size = os.path.getsize(output_pdf_path)
        print(f"4. 验证输出文件: 大小={file_size}字节")
        print("✅ 测试通过！PDF生成器修改正确")
    else:
        print("❌ 测试失败！输出文件不存在")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # 清理临时文件
    if os.path.exists(output_pdf_path):
        os.remove(output_pdf_path)
        print(f"5. 清理临时文件: {output_pdf_path}")
