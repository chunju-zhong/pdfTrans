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
    
    # 提取文本块
    text_blocks = page.get_text("blocks")
    print(f"\n文本块数量: {len(text_blocks)}")
    
    # 收集所有文本块的位置
    text_positions = []
    for i, block in enumerate(text_blocks):
        bbox = block[:4]  # (x0, y0, x1, y1)
        text = block[4].strip()
        if text:
            text_positions.append((bbox, text))
            print(f"文本块 {i+1}: 位置={bbox}, 内容='{text[:30]}...'")
    
    # 检查页面上的绘图对象，重点分析线条
    print(f"\n页面上的绘图对象:")
    drawings = page.get_drawings()
    print(f"绘图对象数量: {len(drawings)}")
    
    # 分析每个绘图对象，重点关注线条
    line_count = 0
    for i, drawing in enumerate(drawings):
        print(f"\n绘图对象 {i+1}:")
        
        # 检查是否有线条
        if "lines" in drawing:
            print(f"  线条数量: {len(drawing['lines'])}")
            for line in drawing["lines"]:
                line_count += 1
                print(f"  线条 {line_count}: {line}")
                
                # 检查这条线是否在某个文本块下方
                line_y = (line[1] + line[3]) / 2  # 线条的平均Y坐标
                for bbox, text in text_positions:
                    # 检查线条是否在文本块下方（误差范围2个单位）
                    if abs(line_y - (bbox[3] - 1)) < 2:
                        # 检查线条长度是否与文本块宽度相近
                        line_length = abs(line[2] - line[0])
                        block_width = bbox[2] - bbox[0]
                        if abs(line_length - block_width) < 10:
                            print(f"    📌 这条线可能是文本块的下划线: '{text[:30]}...'")
        
        # 检查是否有路径
        if "paths" in drawing:
            print(f"  路径数量: {len(drawing['paths'])}")
            for path in drawing["paths"]:
                print(f"  路径: {path}")
        
        # 检查是否有填充
        if "fill" in drawing:
            print(f"  填充颜色: {drawing['fill']}")
        
        # 检查是否有描边
        if "stroke" in drawing:
            print(f"  描边颜色: {drawing['stroke']}")
        
        # 检查线宽
        if "width" in drawing:
            print(f"  线宽: {drawing['width']}")
    
    print(f"\n=== 总计找到 {line_count} 条线 ===")

# 关闭PDF文档
doc.close()