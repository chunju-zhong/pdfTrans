import os
import tempfile
import fitz


def create_test_pdf_with_bookmarks():
    """创建一个带有书签的测试PDF"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_file.close()
    
    doc = fitz.open()
    
    # 第1页：封面（无书签）
    page1 = doc.new_page()
    rect = fitz.Rect(100, 100, 300, 150)
    page1.insert_textbox(rect, "封面", fontsize=12)
    
    # 第2页：目录（无书签）
    page2 = doc.new_page()
    rect = fitz.Rect(100, 100, 300, 150)
    page2.insert_textbox(rect, "目录", fontsize=12)
    
    # 第3页：第1章（有书签）
    page3 = doc.new_page()
    rect = fitz.Rect(100, 100, 300, 150)
    page3.insert_textbox(rect, "第1章 引言", fontsize=12)
    
    # 第4页：第2章（有书签）
    page4 = doc.new_page()
    rect = fitz.Rect(100, 100, 300, 150)
    page4.insert_textbox(rect, "第2章 正文", fontsize=12)
    
    # 添加书签
    toc = [
        [1, "第1章 引言", 3],
        [1, "第2章 正文", 4]
    ]
    doc.set_toc(toc)
    
    doc.save(temp_file.name)
    doc.close()
    
    return temp_file.name


pdf_path = create_test_pdf_with_bookmarks()
print(f"PDF路径: {pdf_path}")

try:
    doc = fitz.open(pdf_path)
    print(f"\nPDF总页数: {doc.page_count}")
    
    for page_num in range(1, doc.page_count + 1):
        print(f"\n=== 第 {page_num} 页 ===")
        page = doc[page_num - 1]
        
        # 使用get_text()
        text = page.get_text()
        print(f"get_text() 结果: '{text}'")
        print(f"get_text() strip后: '{text.strip()}'")
        
        # 使用get_text('blocks')
        blocks = page.get_text('blocks')
        print(f"\nget_text('blocks') 数量: {len(blocks)}")
        for i, block in enumerate(blocks):
            print(f"  块 {i}:")
            print(f"    长度: {len(block)}")
            if len(block) >= 5:
                print(f"    文本: '{block[4]}'")
                print(f"    文本strip后: '{block[4].strip()}'")
                print(f"    文本长度: {len(block[4])}")
    
    doc.close()
finally:
    os.unlink(pdf_path)
