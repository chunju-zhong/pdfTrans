#!/usr/bin/env python3
"""调查 PDF 页面中图像的绘制位置和缩放信息"""
import fitz
import sys
import os

def analyze_page(doc, page_num):
    """分析指定页面的图像绘制信息"""
    page = doc[page_num - 1]
    print(f"\n{'='*60}")
    print(f"第 {page_num} 页分析")
    print(f"{'='*60}")

    # 页面基本信息
    print(f"页面尺寸 (rect): {page.rect.width:.1f} x {page.rect.height:.1f} pt")
    print(f"MediaBox: {page.mediabox}")
    print(f"CropBox: {page.cropbox}")
    print(f"旋转角度: {page.rotation}")

    # 渲染图像尺寸 (DPI=150)
    pix = page.get_pixmap(dpi=150)
    print(f"渲染图像尺寸 (150 DPI): {pix.width} x {pix.height} px")

    # 获取嵌入图像
    images = page.get_images(full=True)
    print(f"\n嵌入图像数量: {len(images)}")

    for idx, img in enumerate(images):
        xref = img[0]
        print(f"\n--- 图像 {idx} (xref={xref}) ---")
        print(f"  图像元数据: width={img[2]}, height={img[3]}, bpc={img[4]}, colorspace={img[5]}")

        # 获取图像在 PDF 页面中的边界框
        rects = page.get_image_rects(xref)
        if rects:
            for r_idx, rect in enumerate(rects):
                print(f"  边界框 [{r_idx}]: x0={rect.x0:.1f}, y0={rect.y0:.1f}, x1={rect.x1:.1f}, y1={rect.y1:.1f}")
                print(f"    宽度={rect.width:.1f}pt, 高度={rect.height:.1f}pt")

                # 计算图像在页面中的占比
                page_w = page.rect.width
                page_h = page.rect.height
                img_w = rect.width
                img_h = rect.height
                print(f"    占页面宽度: {img_w/page_w*100:.1f}%, 占页面高度: {img_h/page_h*100:.1f}%")
                print(f"    左边距: {rect.x0:.1f}pt ({rect.x0/page_w*100:.1f}%)")
                print(f"    上边距: {rect.y0:.1f}pt ({rect.y0/page_h*100:.1f}%)")

                # 计算缩放比例
                orig_w = img[2]
                orig_h = img[3]
                if orig_w > 0 and orig_h > 0:
                    scale_x = img_w * 72 / (orig_w * 96)  # 假设图像 96 DPI
                    scale_y = img_h * 72 / (orig_h * 96)
                    print(f"    估算缩放: x={scale_x:.3f}, y={scale_y:.3f}")
        else:
            print(f"  无法获取边界框")

    # 检查页面是否有文本
    text = page.get_text("text").strip()
    print(f"\n页面文本长度: {len(text)} 字符")
    if text:
        print(f"文本预览: {text[:100]}...")

    # 检查页面是否有绘图命令（可能表示图像是通过绘图命令放置的）
    contents = page.get_contents()
    if contents:
        print(f"\n页面内容流大小: {len(contents)} bytes")
    else:
        print(f"\n页面无内容流")


def main():
    if len(sys.argv) < 2:
        print("用法: python debug_image_placement.py <pdf_path> [page_num]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)

    with fitz.open(pdf_path) as doc:
        total = len(doc)
        print(f"PDF 总页数: {total}")
        print(f"文件: {pdf_path}")

        if page_num:
            analyze_page(doc, page_num)
        else:
            # 分析所有页面
            for pn in range(1, total + 1):
                analyze_page(doc, pn)


if __name__ == '__main__':
    main()
