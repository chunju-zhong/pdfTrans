import fitz
import numpy as np
doc = fitz.open('tests/data/W3PD1098-v1.pdf')
page = doc[5]

# Render at 300 DPI
pix = page.get_pixmap(dpi=300)
arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
gray = np.mean(arr, axis=2)

# Check: what does the bbox [176,85,1234,195] actually cover at 300DPI?
# Compare LLM bbox vs actual text content area
print("=== LLM返回bbox [176, 85, 1234, 195] 与 实际内容对比 ===")
print(f"页面尺寸: 300DPI = {pix.width}x{pix.height}")

# LLM bbox in image
lx0, ly0, lx1, ly1 = 176, 85, 1234, 195
llm_region = gray[ly0:ly1, lx0:lx1]
print(f"LLM bbox区域: ({lx0},{ly0})-({lx1},{ly1}), 宽={lx1-lx0}px, 高={ly1-ly0}px")

# Check what % of text is inside the LLM bbox vs outside
full_dark = gray < 200
in_bbox_dark = full_dark[ly0:ly1, lx0:lx1]
outside_bbox = full_dark.copy()
outside_bbox[ly0:ly1, lx0:lx1] = False

print(f"LLM bbox内暗像素: {np.sum(in_bbox_dark)}")
print(f"bbox外暗像素: {np.sum(outside_bbox)}")
print(f"bbox覆盖的暗像素占比: {np.sum(in_bbox_dark) / (np.sum(in_bbox_dark) + np.sum(outside_bbox)) * 100:.1f}%")

# Check text content in each horizontal band at the text y-range
print(f"\n=== 文本行区域(y=85到195)水平内容分析 ===")
text_strip = gray[85:195, :]
dark_strip = text_strip < 200
col_dark = np.sum(dark_strip, axis=0)
content_start = np.argmax(col_dark > 0)
content_end = len(col_dark) - np.argmax(col_dark[::-1] > 0) - 1
print(f"文本行区域内实际内容: x={content_start}到{content_end}")
print(f"宽度: {content_end - content_start}px")
print(f"LLM返回bbox宽度: {lx1 - lx0}px")
print(f"LLM宽度占实际内容比例: {(lx1-lx0)/(content_end-content_start)*100:.1f}%")
print(f"LLM左边界偏差: {lx0 - content_start}px (LLM超前于实际{lx0 - content_start}px)" if lx0 < content_start else f"LLM左边界偏差: {lx0 - content_start}px (LLM滞后于实际{lx0 - content_start}px)")
print(f"LLM右边界偏差: {lx1 - content_end}px" if lx1 > content_end else f"LLM右边界偏差: {lx1 - content_end}px (短了{content_end - lx1}px)")

# Check the actual image embedded in the PDF
print(f"\n=== 嵌入式图像分析 ===")
images = page.get_images(full=True)
for i, img in enumerate(images):
    xref = img[0]
    base_img = doc.extract_image(xref)
    print(f"Image {i}: w={base_img['width']}, h={base_img['height']}, size={len(base_img['image'])} bytes")
