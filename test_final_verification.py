from modules.pdf_extractor import pdf_extractor

# 提取PDF文本
extraction = pdf_extractor.extract_text('tests/data/test_data_en_text.pdf')

print(f"\n总页数: {extraction.total_pages}")
print("\n" + "="*60)
print("页眉页脚识别结果验证")
print("="*60)

# 遍历所有页面，检查页眉页脚识别情况
all_correct = True
for page in extraction.pages:
    print(f"\n第 {page.page_num} 页:")
    
    # 查找页眉和页脚
    headers = []
    footers = []
    for block in page.text_blocks:
        if not block.is_body_text:
            if block.block_bbox[1] < page.text_blocks[1].block_bbox[1] if len(page.text_blocks) > 1 else True:
                headers.append(block)
            else:
                footers.append(block)
    
    # 打印页眉页脚信息
    if headers:
        print(f"  页眉识别: {len(headers)} 个块")
        for block in headers:
            print(f"    - '{block.block_text}' (字体大小: {block.font_size})")
    
    if footers:
        print(f"  页脚识别: {len(footers)} 个块")
        for block in footers:
            print(f"    - '{block.block_text}' (字体大小: {block.font_size})")
    
    # 检查特定内容是否被正确识别
    for block in page.text_blocks:
        if "Introduction to Agents and Agent architectures" in block.block_text:
            if block.is_body_text:
                print(f"    ❌ 错误: 页眉文本 '{block.block_text}' 被识别为正文")
                all_correct = False
            else:
                print(f"    ✅ 正确: 页眉文本 '{block.block_text}' 被识别为非正文")
        
        if "November 2025" in block.block_text:
            if block.is_body_text:
                print(f"    ❌ 错误: 页脚文本 '{block.block_text}' 被识别为正文")
                all_correct = False
            else:
                print(f"    ✅ 正确: 页脚文本 '{block.block_text}' 被识别为非正文")

print("\n" + "="*60)
if all_correct:
    print("✅ 所有页眉页脚都被正确识别!")
else:
    print("❌ 部分页眉页脚识别错误!")
print("="*60)
