import fitz  # PyMuPDF
import os

# 指定要分析的PDF文件路径
pdf_path = "/Users/chunju/work/pdfTrans/outputs/translated_cef66cae_test_data_en_one_page.pdf"

# 检查文件是否存在
if not os.path.exists(pdf_path):
    print(f"文件不存在: {pdf_path}")
    exit(1)

# 打开PDF文件
doc = fitz.open(pdf_path)
print(f"PDF总页数: {len(doc)}")

# 遍历每一页
for page_num in range(len(doc)):
    page = doc[page_num]
    print(f"\n=== 第 {page_num + 1} 页 ===")
    
    # 提取文本
    text = page.get_text("text")
    print("提取的文本:")
    print(text)
    
    # 检查页面上的绘图对象
    print("\n页面上的绘图对象:")
    drawings = page.get_drawings()
    print(f"绘图对象数量: {len(drawings)}")
    
    # 分析每个绘图对象
    for i, drawing in enumerate(drawings):
        print(f"\n绘图对象 {i+1}:")
        
        # 检查是否有线条
        if "lines" in drawing:
            print(f"  线条数量: {len(drawing['lines'])}")
            for line in drawing["lines"]:
                print(f"  线条: {line}")
        
        # 检查是否有矩形
        if "rects" in drawing:
            print(f"  矩形数量: {len(drawing['rects'])}")
            for rect in drawing["rects"]:
                print(f"  矩形: {rect}")
        
        # 检查是否有填充
        if "fill" in drawing:
            print(f"  填充颜色: {drawing['fill']}")
        
        # 检查是否有描边
        if "stroke" in drawing:
            print(f"  描边颜色: {drawing['stroke']}")
        
        # 检查线宽
        if "width" in drawing:
            print(f"  线宽: {drawing['width']}")
    
    # 检查文本块
    print("\n文本块:")
    text_blocks = page.get_text("blocks")
    print(f"文本块数量: {len(text_blocks)}")
    for i, block in enumerate(text_blocks):
        block_text = block[4].strip()
        if block_text:
            print(f"  文本块 {i+1}: {block_text[:50]}...")

# 关闭PDF文档
doc.close()