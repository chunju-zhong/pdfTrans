# 修复 LLM OCR 字体大小估算及渲染覆盖问题 Spec

## Why

LLM OCR 提取器在估算字体大小时，仅依赖文本中的显式换行符计数行数。DeepSeek-OCR 将多行文本合并为单行返回（无 `\n`），导致行数被低估为 1，字体大小被严重高估（命中 36pt 上限）。这引发三个级联问题：
1. 字体大小过高 → redaction padding 过大 → 遮盖相邻文本块区域
2. 字体大小过高 → 行高倍率计算错误（=1.0）→ 翻译文本溢出或被极度缩小后不可见
3. OCR 返回的 bbox 可能未完全覆盖原文 → redaction 区域不够宽 → 右方露出原文本

## What Changes

- 在 `llm_extractor.py` 中改进字体大小估算：增加基于文本面积的方法，取行数法和面积法的较小值
- 在 `pdf_generator.py` 中增加水平方向 redaction padding，确保原文被完全遮盖

## Impact

- Affected code: `modules/ocr/llm_extractor.py`, `modules/pdf_generator.py`
- Affected specs: `fix-llm-ocr-zero-font-size`（字体大小估算逻辑变更）

## ADDED Requirements

### Requirement: 基于文本面积的字体大小估算

LLM OCR 提取器 SHALL 在估算字体大小时，同时使用行数法和面积法，取较小值作为最终估算结果。

面积法公式：`font_size_by_area = sqrt(bbox_width * bbox_height / (text_length * 0.66))`

其中 `text_length` 为去除换行符后的文本字符数，0.66 为平均字符宽度与行高的乘积系数（Latin 文本约 0.55 宽度比 × 1.2 行高比）。

#### Scenario: 多行文本合并为单行时字体大小估算

- **WHEN** DeepSeek-OCR 返回文本 "There are large variations to how much you can expect to remove in primaries"（75 字符，无换行），bbox 为 (336.0, 249.05, 475.2, 315.27)（宽 139.2pt，高 66.22pt）
- **THEN** 行数法估算 font_size = min(66.22 / 1 * 0.75, 36) = 36（命中上限）
- **AND** 面积法估算 font_size = sqrt(139.2 * 66.22 / (75 * 0.66)) = sqrt(186.3) ≈ 13.6
- **AND** 最终 font_size = min(36, 13.6) = 13.6

#### Scenario: 短文本标题字体大小估算

- **WHEN** DeepSeek-OCR 返回文本 "Lesson:"（7 字符），bbox 为 (336.0, 202.02, 372.48, 220.73)（宽 36.48pt，高 18.71pt）
- **THEN** 行数法估算 font_size = min(18.71 / 1 * 0.75, 36) = 14.0
- **AND** 面积法估算 font_size = sqrt(36.48 * 18.71 / (7 * 0.66)) = sqrt(147.7) ≈ 12.2
- **AND** 最终 font_size = min(14.0, 12.2) = 12.2

#### Scenario: 单行短文本（面积法结果大于行数法）

- **WHEN** 文本 "Removal of the primary depends on the raw water characteristics"（63 字符），bbox 高 31.19pt，宽 425.28pt
- **THEN** 行数法估算 font_size = min(31.19 * 0.75, 36) = 23.4
- **AND** 面积法估算 font_size = sqrt(425.28 * 31.19 / (63 * 0.66)) = sqrt(318.5) ≈ 17.8
- **AND** 最终 font_size = min(23.4, 17.8) = 17.8

### Requirement: 增大水平方向 redaction padding

PDF 生成器 SHALL 对水平方向使用更大的 redaction padding，确保 OCR 返回的 bbox 未完全覆盖的原文也被遮盖。

- 水平 padding: `max(5, min(font_size * 0.5, 12))`
- 垂直 padding: `max(3, min(font_size * 0.3, 6))`

#### Scenario: 标题块 redaction 区域扩展

- **WHEN** 文本块 font_size=18，bbox=(26.88, 44.63, 270.24, 68.62)
- **THEN** 水平 padding = max(5, min(18*0.5, 12)) = 9
- **AND** 垂直 padding = max(3, min(18*0.3, 6)) = 5.4
- **AND** redaction rect = (26.88-9, 44.63-5.4, 270.24+9, 68.62+5.4) = (17.88, 39.23, 279.24, 74.02)

## MODIFIED Requirements

### Requirement: LLM OCR 字体大小估算（原 fix-llm-ocr-zero-font-size）

LLM OCR 提取器 SHALL 使用改进的字体大小估算方法，同时考虑行数和文本面积，取较小值。

原公式：`font_size = max(6, min(bbox_height / num_lines * 0.75, 36))`

新公式：
```python
font_size_by_lines = bbox_height / num_lines * 0.75
font_size_by_area = sqrt(bbox_width * bbox_height / (text_length * 0.66))
font_size = max(6, min(font_size_by_lines, font_size_by_area, 36))
```

此修改同时应用于 `_parse_ref_tags_response` 和 `_parse_json_response` 方法。
