from modules.pdf_extractor import pdf_extractor

# 提取PDF文本
extraction = pdf_extractor.extract_text('tests/data/test_data_en_text.pdf')

# 遍历所有页面和文本块
for page in extraction.pages:
    print(f"\nPage {page.page_num}:")
    for block in page.text_blocks:
        print(f"  Block {block.block_no}: '{block.block_text}'")
        print(f"    Font Size: {block.font_size}")
        print(f"    Position: {block.block_bbox}")
        print(f"    Is Body Text: {block.is_body_text}")
        print(f"    Font: {block.font}")
        print(f"    Bold: {block.bold}")
        print(f"    Italic: {block.italic}")
