# 修复 OCR 输出 PDF 字号偏大超出文本框

## 问题

OCR 模式下输出 PDF 的翻译文字字号偏大，超出文本框范围。

## 根因

`paddle_extractor.py` 第 380 行的 font_size 估算公式偏大：

```python
estimated_font_size = max(8, min(24, (bbox_height / num_lines) * 0.8))
```

问题分析：
1. `bbox_height` 是整个文本块的 PDF 点坐标高度，包含了行间距
2. 乘以 0.8 的系数不够——实际行间距通常占行高的 20-40%
3. 翻译后的中文文本通常比英文原文占用更多空间，但字号没有相应缩小
4. `pdf_generator.py` 第 265 行直接使用 `original_font_size` 作为初始字号，前 3 次尝试不缩小字号

## 修改方案

### 修改 1: 降低 OCR font_size 估算系数

**文件**: `/Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py` 第 380 行

将 `0.8` 系数降低为 `0.6`，更接近实际字号与行高的比例：

```python
# 修改前
estimated_font_size = max(8, min(24, (bbox_height / num_lines) * 0.8))

# 修改后
estimated_font_size = max(6, min(20, (bbox_height / num_lines) * 0.6))
```

同时降低上限从 24 到 20，降低下限从 8 到 6，使字号范围更保守。

### 修改 2: 公式字号同样降低系数

**文件**: `/Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py` 第 509 行

```python
# 修改前
estimated_font_size = max(8, min(20, bbox_height * 0.8))

# 修改后
estimated_font_size = max(6, min(16, bbox_height * 0.6))
```

## 验证

1. 上传扫描版 PDF，启用 OCR 模式翻译
2. 检查输出 PDF：翻译文本应在文本框内，不溢出
3. 字号应与原文视觉上接近
