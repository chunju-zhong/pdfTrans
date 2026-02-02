#!/usr/bin/env python3

import os
import sys
import logging
from modules.pdf_extractor import PdfExtractor
from utils.logging_config import setup_logging

# 配置日志
setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别，查看详细日志

def test_style_extraction():
    """测试PDF提取模块是否能正确提取样式信息"""
    # 测试文件路径
    test_file = '/Users/chunju/work/pdfTrans/tests/data/IntroductionToAgents.pdf'
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False
    
    try:
        # 创建本地PDF提取器实例
        pdf_extractor = PdfExtractor(test_file)
        # 调用extract_text方法，提取第一页的文本块
        pdf_page = pdf_extractor.extract_text(pages=[1]).pages[0]
        
        # 打印提取的文本块数量
        print(f"提取到 {len(pdf_page.text_blocks)} 个文本块")
        
        # 检查每个文本块的样式信息
        all_styles_empty = True
        for i, text_block in enumerate(pdf_page.text_blocks):
            print(f"\n文本块 {i+1}:")
            print(f"  文本: '{text_block.block_text[:50]}...'")
            print(f"  块编号: {text_block.block_no}")
            print(f"  位置: {text_block.block_bbox}")
            print(f"  字体: '{text_block.font}'")
            print(f"  大小: {text_block.font_size}")
            print(f"  颜色: {text_block.color}")
            print(f"  粗体: {text_block.bold}")
            print(f"  斜体: {text_block.italic}")
            
            # 检查样式信息是否为空
            if text_block.font or text_block.font_size > 0:
                all_styles_empty = False
        
        if all_styles_empty:
            print("\n❌ 所有文本块的样式信息为空")
            return False
        else:
            print("\n✅ 部分或全部文本块的样式信息已正确提取")
            return True
    except Exception as e:
        print(f"\n❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 运行测试
    success = test_style_extraction()
    sys.exit(0 if success else 1)
