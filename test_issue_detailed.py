from modules.pdf_extractor import pdf_extractor
import logging

# 设置日志级别为DEBUG以查看详细日志
logging.basicConfig(level=logging.DEBUG)

# 提取PDF文本
extraction = pdf_extractor.extract_text('tests/data/test_data_en_text.pdf')

print(f"\n总页数: {extraction.total_pages}")

# 遍历所有页面和文本块
for page in extraction.pages[:5]:  # 只查看前5页
    print(f"\n=== 第 {page.page_num} 页 ===")
    for block in page.text_blocks:
        print(f"\n  Block {block.block_no}:")
        print(f"    Text: '{block.block_text}'")
        print(f"    Font Size: {block.font_size}")
        print(f"    Position: {block.block_bbox}")
        print(f"    Is Body Text: {block.is_body_text}")
        print(f"    Font: {block.font}")
        print(f"    Bold: {block.bold}")
        print(f"    Italic: {block.italic}")

print(f"\n=== 所有页面的页眉页脚统计 ===")
header_footer_blocks = []
body_text_blocks = []

for page in extraction.pages:
    for block in page.text_blocks:
        if not block.is_body_text:
            header_footer_blocks.append((page.page_num, block))
        else:
            body_text_blocks.append((page.page_num, block))

print(f"\n非正文文本块总数: {len(header_footer_blocks)}")
print(f"正文文本块总数: {len(body_text_blocks)}")

print(f"\n非正文文本块详情:")
for page_num, block in header_footer_blocks:
    print(f"  第 {page_num} 页: '{block.block_text}'")
