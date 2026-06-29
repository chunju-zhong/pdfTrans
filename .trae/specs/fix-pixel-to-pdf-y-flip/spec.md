# 修复 `_pixel_to_pdf_coords` 缺乏 Y 轴翻转 Spec

> **⚠️ 已废弃（2026-06-24）**：用户确认 LLM OCR 和普通模式都不需要 Y 轴翻转。PDF 的 Y 轴翻转是 PyMuPDF 内部渲染机制，不应在 OCR 坐标转换中额外处理。相关代码已还原。详见 [fix-llm-ocr-tibetan-bbox-width](../fix-llm-ocr-tibetan-bbox-width/spec.md)。

## Why
Qwen3.7-Plus 等通用 VLM 模型返回的 bbox 坐标基于图像坐标系（左上角原点，Y 向下增长），但 PDF 坐标系使用左下角原点（Y 向上增长）。`_pixel_to_pdf_coords` 直接缩放像素坐标而不翻转 Y 轴，导致文本框出现在错误位置——图像顶部的文字被放到 PDF 底部。

## 根因分析

### 日志数据
```
第6页: 页面=1191.0x231.8pt, 图像=4963x966px
LLM返回像素bbox: [176, 85, 1234, 195]  (图像左上角原点的坐标)
PDF bbox(当前):   (42.2, 20.4, 296.1, 46.8)  ← y=20.4~46.8 在页面底部
PDF bbox(正确):   (42.2, 185.0, 296.1, 211.4) ← y=185~211 在页面顶部
```

### 坐标系统差异
| 系统 | 原点 | Y 方向 |
|------|------|--------|
| 图像 | 左上角 (0,0) | 向下增长 |
| PDF (PyMuPDF) | 左下角 (0,0) | 向上增长 |
| 浮窗显示 (浏览器) | 左上角 (0,0) | 向下增长 |

### 当前代码问题
```python
# 当前：直接缩放，没有翻转 Y 轴
return (x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y)

# 应该：先翻转 Y 轴再缩放
pdf_y1 = (img_height - y2) * scale_y  # 图像底部 → PDF 底部
pdf_y2 = (img_height - y1) * scale_y  # 图像顶部 → PDF 顶部
return (x1 * scale_x, pdf_y1, x2 * scale_x, pdf_y2)
```

### 影响
- 文本渲染位置错误：本应在页面顶部的文字渲染到底部
- redaction 删除原文的位置也错误，删错了区域
- 归一化坐标路径也存在同样的 Y 轴翻转缺失问题

## What Changes
- 修复 `_pixel_to_pdf_coords` 中像素坐标的 Y 轴翻转（`is_normalized=False`）
- 修复 `_pixel_to_pdf_coords` 中归一化坐标的 Y 轴翻转（`is_normalized=True`）
- 增强坐标转换日志，便于调试

## Impact
- Affected code:
  - `modules/ocr/llm_extractor.py` — `_pixel_to_pdf_coords` 方法
  - `modules/ocr/paddle_extractor.py` — `_pixel_to_pdf_coords`（同样方法，同样 Bug）
- 同时影响 LLM OCR 和 PaddleOCR 的场景

## ADDED Requirements

### Requirement: 像素坐标 Y 轴翻转
`_pixel_to_pdf_coords(is_normalized=False)` SHALL 在缩放像素坐标前将 Y 轴从图像坐标系（左上角原点）翻转到 PDF 坐标系（左下角原点）。

#### Scenario: 像素坐标正确翻转
- **GIVEN** 图像尺寸 `img_height=966px`, 页面高度 `page_height=231.8pt`
- **WHEN** 转换像素 bbox `[176, 85, 1234, 195]`
- **THEN** PDF y 坐标应为 `pdf_y1=(966-195)*231.8/966=185.0`, `pdf_y2=(966-85)*231.8/966=211.4`

### Requirement: 归一化坐标 Y 轴翻转
`_pixel_to_pdf_coords(is_normalized=True)` SHALL 在缩放归一化坐标前将 Y 轴翻转。

#### Scenario: 归一化坐标正确翻转
- **GIVEN** 页面高度 `page_height=792pt`
- **WHEN** 转换归一化 bbox `[100, 100, 500, 800]`
- **THEN** PDF y 坐标应为 `pdf_y1=(999-800)/999*792`, `pdf_y2=(999-100)/999*792`

### Requirement: 坐标转换日志增强
LLM OCR 提取日志 SHALL 记录坐标转换的参数（像素坐标、缩放因子、PDF 坐标）。

#### Scenario: 坐标转换有日志
- **WHEN** LLM OCR 提取完一页
- **THEN** 日志中至少有一个 text_block 的原始像素 bbox 和转换后的 PDF bbox