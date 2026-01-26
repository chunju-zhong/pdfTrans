from modules.pdf_extractor import pdf_extractor
import logging

# 设置日志级别为INFO以查看详细日志
logging.basicConfig(level=logging.INFO)

# 提取PDF文本
extraction = pdf_extractor.extract_text('tests/data/test_data_en_text.pdf')

print(f"\n总页数: {extraction.total_pages}")

# 遍历所有页面，特别关注第2页
for page in extraction.pages:
    print(f"\n=== 第 {page.page_num} 页 ===")
    
    header_found = False
    footer_found = False
    
    for block in page.text_blocks:
        print(f"\n  块 {block.block_no}:")
        print(f"    文本: '{block.block_text}'")
        print(f"    字体大小: {block.font_size}")
        print(f"    位置: {block.block_bbox}")
        print(f"    是否为正文: {'是' if block.is_body_text else '否'}")
        print(f"    字体: {block.font}")
        print(f"    粗体: {block.bold}")
        print(f"    斜体: {block.italic}")
        
        # 检查特定内容
        if "Introduction to Agents and Agent architectures" in block.block_text:
            print(f"    🔍 识别为页眉")
            header_found = True
        
        if "November 2025" in block.block_text:
            print(f"    🔍 识别为页脚")
            footer_found = True
    
    print(f"\n  页面统计:")
    print(f"    总文本块数: {len(page.text_blocks)}")
    print(f"    正文文本块数: {sum(1 for block in page.text_blocks if block.is_body_text)}")
    print(f"    非正文文本块数: {sum(1 for block in page.text_blocks if not block.is_body_text)}")
    print(f"    页眉识别: {'✅ 找到' if header_found else '❌ 未找到'}")
    print(f"    页脚识别: {'✅ 找到' if footer_found else '❌ 未找到'}")

print(f"\n=== 总结 ===")
total_blocks = sum(len(page.text_blocks) for page in extraction.pages)
total_body_blocks = sum(1 for page in extraction.pages for block in page.text_blocks if block.is_body_text)
total_non_body_blocks = sum(1 for page in extraction.pages for block in page.text_blocks if not block.is_body_text)

print(f"\n  总文本块数: {total_blocks}")
print(f"  正文文本块数: {total_body_blocks}")
print(f"  非正文文本块数: {total_non_body_blocks}")
print(f"  非正文文本块占比: {total_non_body_blocks/total_blocks*100:.1f}%")
