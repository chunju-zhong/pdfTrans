# 修复日期型页尾未被识别导致跨页错误合并 Spec

## Why

非 OCR 模式下，页尾日期文本（如 "2025年2月 8"、"2025年2月 9"）未被 `text_analyzer.py` 识别为页脚，导致这些文本保持 `is_body_text=True`，在语义合并阶段与下一页的正文开头被错误合并为一个 MergedBlock，翻译后页尾内容混入正文。

## What Changes

- **移除短文本 100% 完全相同阈值**：将 `_add_similar_blocks()` 中短文本（< 20 字符）的相似度阈值从 1.0 降低到 0.85

## Impact

- Affected code: `modules/extractors/text_analyzer.py` 的 `_add_similar_blocks` 函数
- 行为变更：短文本页眉页脚检测更宽松，相似但不完全相同的短文本（如递增日期）将被识别为非正文

## 根因分析

### 当前短文本相似度阈值过高

`_add_similar_blocks()` 中，当两个文本块长度均 < 20 字符时，要求相似度 = 100%（完全相同）才标记为页眉页脚。这是之前为修复误判问题（"xii | Foreword" 和 "xiv | Foreword" 被误判）而引入的。

但这个阈值过于严格，导致合法的日期型页脚无法被检测：
- "2025年2月 8" 与 "2025年2月 9"：LCS 相似度 = 8/9 ≈ 88.9%，低于 100% 阈值
- 这些文本位于页面底部 15% 区域，且在多个页面重复出现（仅末尾数字不同），符合页脚特征

### "xii | Foreword" 误判问题回顾

之前 "xii | Foreword" 和 "xiv | Foreword" 的 LCS 相似度为 92.9%，被标记为非正文。当时的判断认为这是误判，因此将短文本阈值提高到 100%。但实际上，"xii | Foreword" 和 "xiv | Foreword" 本身就是页脚格式的页码标注，标记为非正文是正确行为。因此，将短文本阈值降回 0.85 不会引入新的误判。

## MODIFIED Requirements

### Requirement: _add_similar_blocks 函数短文本阈值

`_add_similar_blocks()` SHALL 将短文本（两个文本块长度均 < 20 字符）的相似度阈值从 1.0 修改为 0.85。

修改前：
```python
if both_short:
    threshold = 1.0  # 短文本仅当完全相同时才标记为非正文
elif mixed_length:
    threshold = 0.95
else:
    threshold = 0.9
```

修改后：
```python
if both_short:
    threshold = 0.85  # 短文本使用 0.85 阈值，覆盖日期型页尾
elif mixed_length:
    threshold = 0.95
else:
    threshold = 0.9
```

#### Scenario: 日期型页尾被正确识别

- **WHEN** "2025年2月 8" 与 "2025年2月 9" 位于不同页面的底部 15% 区域
- **AND** LCS 相似度 ≈ 88.9% > 85%
- **THEN** 被正确标记为非正文

#### Scenario: 页码标注被正确识别

- **WHEN** "xii | Foreword" 与 "xiv | Foreword" 位于页面底部区域
- **AND** LCS 相似度 ≈ 92.9% > 85%
- **THEN** 被标记为非正文（正确行为，它们确实是页脚）

#### Scenario: 不相似的短文本不被误判

- **WHEN** 两个短文本 LCS 相似度 < 85%
- **THEN** 不被标记为非正文

## REMOVED Requirements

### Requirement: 短文本仅当完全相同时才标记为非正文

**Reason**: 该要求过于严格，导致合法的日期型页脚无法被检测
**Migration**: 短文本使用 0.85 阈值
