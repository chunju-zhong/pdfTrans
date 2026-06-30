#!/usr/bin/env python3
"""分析 PDF 坐标系统：检查 Y 轴方向、坐标原点等"""
import fitz
import sys

def analyze_coord_system(doc, page_num):
    page = doc[page_num - 1]
    print(f"\n{'='*60}")
    print(f"第 {page_num} 页坐标系统分析")
    print(f"{'='*60}")

    # 1. 页面坐标系
    print(f"\n1. 页面坐标系:")
    print(f"   page.rect = {page.rect}")
    print(f"   page.mediabox = {page.mediabox}")
    print(f"   page.cropbox = {page.cropbox}")
    print(f"   page.rotation = {page.rotation}")

    # 2. PyMuPDF 的坐标原点
    # 在 PyMuPDF 中，page.rect.y0 通常是 0（底部），y1 是页面高度
    # 但有些 PDF 的 y0 可能是负数
    print(f"\n2. 坐标原点:")
    print(f"   rect.x0={page.rect.x0}, rect.y0={page.rect.y0}")
    print(f"   rect.x1={page.rect.x1}, rect.y1={page.rect.y1}")
    print(f"   → PDF 坐标系: 原点=({page.rect.x0}, {page.rect.y0}), Y轴向上")

    # 3. 渲染图像的坐标系统
    pix = page.get_pixmap(dpi=150)
    print(f"\n3. 渲染图像 (150 DPI):")
    print(f"   尺寸: {pix.width} x {pix.height} px")
    print(f"   → 图像坐标系: 原点=左上角(0,0), Y轴向下")

    # 4. 坐标转换分析
    page_w = page.rect.width
    page_h = page.rect.height
    img_w = pix.width
    img_h = pix.height

    print(f"\n4. 坐标转换分析:")
    print(f"   页面: {page_w:.1f} x {page_h:.1f} pt")
    print(f"   图像: {img_w} x {img_h} px")

    # 假设 DeepSeek-OCR 返回归一化坐标（基于图像，原点在左上角）
    # 测试几个点
    test_points = [
        ("左上角", 0, 0),
        ("右上角", 999, 0),
        ("左下角", 0, 999),
        ("右下角", 999, 999),
        ("中心", 500, 500),
        ("顶部1/4处", 500, 250),
        ("底部1/4处", 500, 750),
    ]

    print(f"\n5. 归一化坐标 → PDF 坐标映射（当前逻辑，无 Y-flip）:")
    for name, nx, ny in test_points:
        pdf_x = nx / 999 * page_w
        pdf_y = ny / 999 * page_h
        print(f"   {name} ({nx}, {ny}) → PDF ({pdf_x:.1f}, {pdf_y:.1f})")

    print(f"\n6. 归一化坐标 → PDF 坐标映射（加 Y-flip）:")
    for name, nx, ny in test_points:
        pdf_x = nx / 999 * page_w
        pdf_y = (999 - ny) / 999 * page_h  # Y-flip
        print(f"   {name} ({nx}, {ny}) → PDF ({pdf_x:.1f}, {pdf_y:.1f})")

    # 7. 关键问题：PDF 的 Y 轴方向
    print(f"\n7. 关键分析:")
    print(f"   PDF 坐标系: Y=0 在底部, Y={page_h:.1f} 在顶部")
    print(f"   图像坐标系: Y=0 在顶部, Y={img_h} 在底部")
    print(f"   → 如果不做 Y-flip，图像顶部的文本会被映射到 PDF 底部！")

    # 8. 检查页面是否有旋转
    if page.rotation != 0:
        print(f"\n8. 警告: 页面有 {page.rotation}° 旋转，需要额外处理！")
    else:
        print(f"\n8. 页面无旋转")

    # 9. 获取页面实际内容位置（如果有文本）
    blocks = page.get_text("dict")["blocks"]
    if blocks:
        print(f"\n9. 页面文本块位置:")
        for i, block in enumerate(blocks[:5]):  # 只显示前5个
            if "lines" in block:
                bbox = block["bbox"]
                print(f"   块{i}: bbox={bbox}")
                print(f"      → 在 PDF 中的位置: x=[{bbox[0]:.1f}, {bbox[2]:.1f}], y=[{bbox[1]:.1f}, {bbox[3]:.1f}]")
    else:
        print(f"\n9. 页面无文本块（扫描页）")


def main():
    if len(sys.argv) < 2:
        print("用法: python debug_coord_system.py <pdf_path> [page_num]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    with fitz.open(pdf_path) as doc:
        analyze_coord_system(doc, page_num)


if __name__ == '__main__':
    main()
