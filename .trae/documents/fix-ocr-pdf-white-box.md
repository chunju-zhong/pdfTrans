# 修复 OCR 翻译后 PDF 输出白框问题

## 问题摘要

OCR 识别翻译后输出 PDF 只显示白色框，没有文字，且未覆盖原文。

## 根因分析

两个核心 Bug：

### Bug 1: bbox 坐标系不匹配（主因）

| 管道 | bbox 坐标系 | 范围示例 |
|------|-----------|---------|
| 正常提取器 (PyMuPDF) | PDF 点坐标 | (0, 0, 595, 842) |
| OCR 提取器 (PaddleOCR) | 图像像素坐标 | (0, 0, 1240, 1754) |
| PDF 写入器期望 | PDF 点坐标 | (0, 0, 595, 842) |

OCR 提取器在 `_process_page_layout` 中直接使用 PaddleOCR 返回的像素坐标存入 `TextBlock.bbox`，但 PDF 写入器 (`pdf_generator.py`) 将 bbox 当作 PDF 点坐标使用，导致白色矩形和翻译文本都画在页面范围外。

**转换公式**：
```
scale_x = page_width_pts / image_width_px
scale_y = page_height_pts / image_height_px
pdf_x = pixel_x * scale_x
pdf_y = pixel_y * scale_y
```

### Bug 2: font_size 为 0

OCR 提取器创建的 TextBlock 中 `font_size` 默认为 `0.0`（PaddleOCR 不提供字体大小），PDF 写入器用 `font_size=0` 渲染翻译文本，完全不可见。

**修复方案**：根据 bbox 高度和文本行数估算 font_size：
```
estimated_font_size = (bbox_height_pts / num_lines) * 0.8
```

## 修改方案

### 修改 1: 在 paddle_extractor.py 中添加坐标转换

**文件**: `/Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py`

**方法**: 在 `extract_from_pdf()` 中，渲染页面后记录每页的图像尺寸和 PDF 页面尺寸，然后在 `_process_page_layout()`、`_process_page_tables()`、`_process_page_formulas()` 中将像素坐标转换为 PDF 点坐标。

具体实现：

1. `_render_pages()` 返回值增加页面尺寸信息：
   ```python
   # 当前返回: {page_num: img_path}
   # 修改为返回: {page_num: {'img_path': path, 'page_width_pts': w, 'page_height_pts': h, 'img_width_px': iw, 'img_height_px': ih}}
   ```

2. 新增 `_pixel_to_pdf_coords(bbox, page_info)` 方法：
   ```python
   def _pixel_to_pdf_coords(self, bbox, page_info):
       scale_x = page_info['page_width_pts'] / page_info['img_width_px']
       scale_y = page_info['page_height_pts'] / page_info['img_height_px']
       x1, y1, x2, y2 = bbox
       return (x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y)
   ```

3. 在 `_process_page_layout()` 中，创建 TextBlock 时转换坐标：
   ```python
   pdf_bbox = self._pixel_to_pdf_coords((float(x1), float(y1), float(x2), float(y2)), page_info)
   tb = TextBlock(block_no=block_no, text=text.strip(), bbox=pdf_bbox, ...)
   ```

4. 同样在 `_process_page_tables()` 和 `_process_page_formulas()` 中转换坐标

5. `_extract_image_for_region()` 中的 bbox 也需要转换

### 修改 2: 估算 OCR 文本的 font_size

**文件**: `/Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py`

在 `_process_page_layout()` 中，创建 TextBlock 时根据 bbox 高度估算 font_size：

```python
# bbox 已转换为 PDF 点坐标
bbox_height = pdf_bbox[3] - pdf_bbox[1]
num_lines = max(1, text.strip().count('\n') + 1)
estimated_font_size = max(8, min(24, (bbox_height / num_lines) * 0.8))

tb = TextBlock(
    block_no=block_no,
    text=text.strip(),
    bbox=pdf_bbox,
    block_type=0,
    page_num=page_num,
    font_size=estimated_font_size,
)
```

### 修改 3: 传递 page_info 到各处理方法

**文件**: `/Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py`

修改 `_process_page_layout`、`_process_page_tables`、`_process_page_formulas` 的签名，增加 `page_info` 参数：

```python
def _process_page_layout(self, pipeline, img_path, page_num, page_info):
def _process_page_tables(self, pipeline, img_path, page_num, layout_data, page_info):
def _process_page_formulas(self, pipeline, img_path, page_num, layout_data, page_info):
```

在 `extract_from_pdf()` 中调用时传入对应的 `page_info`。

## 验证步骤

1. 上传扫描版 PDF，启用 OCR 模式翻译
2. 检查输出 PDF：翻译文本应正确显示在原文位置上
3. 白色矩形应精确覆盖原文区域
4. 翻译文本字号应与原文大致匹配
5. 表格和公式区域的 bbox 也应正确转换
