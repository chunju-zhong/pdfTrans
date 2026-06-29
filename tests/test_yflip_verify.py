"""验证 Y 轴翻转修复：第6页的坐标转换是否正确"""
import sys
sys.path.insert(0, '.')

# 模拟第6页数据
page_info = {
    'page_width_pts': 1191.0,
    'page_height_pts': 231.8,
    'img_width_px': 4963,
    'img_height_px': 966,
}

bbox_pixel = (176, 85, 1234, 195)  # LLM OCR 返回的像素坐标

from modules.ocr.llm_extractor import LlmOcrExtractor
extractor = LlmOcrExtractor()

# 测试像素坐标路径 (is_normalized=False)
result_pixel = extractor._pixel_to_pdf_coords(bbox_pixel, page_info, is_normalized=False)
print(f"像素坐标路径:")
print(f"  输入 bbox:      {bbox_pixel}")
print(f"  输出 PDF bbox:  ({result_pixel[0]:.2f}, {result_pixel[1]:.2f}, {result_pixel[2]:.2f}, {result_pixel[3]:.2f})")
print(f"  预期 Y 范围:    185.0 ~ 211.4 (页面顶部)")
print(f"  Y 正确?         {'✓' if 180 < result_pixel[1] < 190 and 205 < result_pixel[3] < 215 else '✗'}")
print()

# 测试归一化坐标路径 (is_normalized=True)
bbox_norm = (176, 85, 1234, 195)  # 模拟归一化坐标
result_norm = extractor._pixel_to_pdf_coords(bbox_norm, page_info, is_normalized=True)
print(f"归一化坐标路径:")
print(f"  输入 bbox:      {bbox_norm}")
print(f"  输出 PDF bbox:  ({result_norm[0]:.2f}, {result_norm[1]:.2f}, {result_norm[2]:.2f}, {result_norm[3]:.2f})")
print()

# 验证旧行为 (无翻转) vs 新行为 (有翻转)
print("---")
print("旧行为 (无翻转): y=20.4~46.8 → 文本在页面底部 (错误)")
print(f"新行为 (有翻转): y={result_pixel[1]:.1f}~{result_pixel[3]:.1f} → 文本在页面顶部 (正确)")
