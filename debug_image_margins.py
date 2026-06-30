#!/usr/bin/env python3
"""分析原始扫描图像是否有白边"""
import fitz
import numpy as np
import sys

def analyze_image_margins(doc, page_num, dpi=150):
    page = doc[page_num - 1]
    print(f"\n{'='*60}")
    print(f"第 {page_num} 页图像白边分析")
    print(f"{'='*60}")

    # 获取页面尺寸
    page_w = page.rect.width
    page_h = page.rect.height
    print(f"页面尺寸: {page_w:.1f} x {page_h:.1f} pt")

    # 渲染高分辨率图像
    pix = page.get_pixmap(dpi=dpi)
    img_w, img_h = pix.width, pix.height
    print(f"渲染图像 ({dpi} DPI): {img_w} x {img_h} px")

    # 转为 numpy 数组
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(img_h, img_w, pix.n)

    # 如果是 RGBA，转灰度
    if pix.n >= 3:
        gray = np.mean(img[:,:,:3], axis=2)
    else:
        gray = img[:,:,0]

    # 检测白边阈值（接近白色的像素）
    threshold = 240

    # 分析四边
    # 上边
    top_margin = 0
    for y in range(img_h):
        row = gray[y, :]
        white_ratio = np.mean(row > threshold)
        if white_ratio < 0.9:  # 非白边
            top_margin = y
            break

    # 下边
    bottom_margin = 0
    for y in range(img_h - 1, -1, -1):
        row = gray[y, :]
        white_ratio = np.mean(row > threshold)
        if white_ratio < 0.9:
            bottom_margin = img_h - 1 - y
            break

    # 左边
    left_margin = 0
    for x in range(img_w):
        col = gray[:, x]
        white_ratio = np.mean(col > threshold)
        if white_ratio < 0.9:
            left_margin = x
            break

    # 右边
    right_margin = 0
    for x in range(img_w - 1, -1, -1):
        col = gray[:, x]
        white_ratio = np.mean(col > threshold)
        if white_ratio < 0.9:
            right_margin = img_w - 1 - x
            break

    print(f"\n白边分析 (阈值={threshold}):")
    print(f"  上边: {top_margin}px ({top_margin/img_h*100:.1f}%)")
    print(f"  下边: {bottom_margin}px ({bottom_margin/img_h*100:.1f}%)")
    print(f"  左边: {left_margin}px ({left_margin/img_w*100:.1f}%)")
    print(f"  右边: {right_margin}px ({right_margin/img_w*100:.1f}%)")

    # 内容区域
    content_x0 = left_margin
    content_y0 = top_margin
    content_x1 = img_w - right_margin
    content_y1 = img_h - bottom_margin
    content_w = content_x1 - content_x0
    content_h = content_y1 - content_y0

    print(f"\n内容区域:")
    print(f"  像素: ({content_x0}, {content_y0}) - ({content_x1}, {content_y1})")
    print(f"  尺寸: {content_w} x {content_h} px")
    print(f"  占图像: {content_w/img_w*100:.1f}% x {content_h/img_h*100:.1f}%")

    # 转换为 PDF 坐标
    scale_x = page_w / img_w
    scale_y = page_h / img_h
    pdf_x0 = content_x0 * scale_x
    pdf_y0 = content_y0 * scale_y
    pdf_x1 = content_x1 * scale_x
    pdf_y1 = content_y1 * scale_y

    print(f"\n内容区域 PDF 坐标:")
    print(f"  ({pdf_x0:.1f}, {pdf_y0:.1f}) - ({pdf_x1:.1f}, {pdf_y1:.1f}) pt")
    print(f"  尺寸: {pdf_x1-pdf_x0:.1f} x {pdf_y1-pdf_y0:.1f} pt")

    # 如果有白边，计算归一化坐标的偏移
    if left_margin > 0 or top_margin > 0 or right_margin > 0 or bottom_margin > 0:
        print(f"\n⚠️ 检测到白边！")
        print(f"归一化坐标需要调整:")
        print(f"  原始: pdf = norm / 999 * page_size")
        print(f"  修正: pdf = content_offset + norm / 999 * content_size")
        print(f"  其中 content_offset = ({pdf_x0:.1f}, {pdf_y0:.1f})")
        print(f"       content_size = ({pdf_x1-pdf_x0:.1f}, {pdf_y1-pdf_y0:.1f})")

        # 示例：假设归一化坐标 [100, 100, 500, 200]
        norm_bbox = (100, 100, 500, 200)
        # 原始转换
        orig_pdf = (
            norm_bbox[0] / 999 * page_w,
            norm_bbox[1] / 999 * page_h,
            norm_bbox[2] / 999 * page_w,
            norm_bbox[3] / 999 * page_h,
        )
        # 修正转换
        corr_pdf = (
            pdf_x0 + norm_bbox[0] / 999 * (pdf_x1 - pdf_x0),
            pdf_y0 + norm_bbox[1] / 999 * (pdf_y1 - pdf_y0),
            pdf_x0 + norm_bbox[2] / 999 * (pdf_x1 - pdf_x0),
            pdf_y0 + norm_bbox[3] / 999 * (pdf_y1 - pdf_y0),
        )
        print(f"\n示例归一化坐标 {norm_bbox}:")
        print(f"  原始转换: ({orig_pdf[0]:.1f}, {orig_pdf[1]:.1f}, {orig_pdf[2]:.1f}, {orig_pdf[3]:.1f})")
        print(f"  修正转换: ({corr_pdf[0]:.1f}, {corr_pdf[1]:.1f}, {corr_pdf[2]:.1f}, {corr_pdf[3]:.1f})")
        print(f"  偏移: ({corr_pdf[0]-orig_pdf[0]:.1f}, {corr_pdf[1]-orig_pdf[1]:.1f})")
    else:
        print(f"\n✅ 无白边，图像内容覆盖整个页面")


def main():
    if len(sys.argv) < 2:
        print("用法: python debug_image_margins.py <pdf_path> [page_num]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    with fitz.open(pdf_path) as doc:
        analyze_image_margins(doc, page_num)


if __name__ == '__main__':
    main()
