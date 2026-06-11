# 修复合并块拆分后 bbox 高度过大导致文本溢出和段落遮挡 Spec

## Why

17-18页翻译后的PDF字体大小偏大，段落最后一行无法完全显示，且下一段落的白色背景遮挡上一段落的前半部分。根因是合并块拆分时，所有拆分块统一使用 `max_height`（合并组中最大单块高度）作为 bbox 高度，导致小高度块的 bbox 向下扩展，侵入下一块的视觉区域。同时 PDF 生成器前两次渲染尝试使用比原始字体大 10%-20% 的字体大小，进一步加剧溢出。

## 根因分析

### 问题1：合并块拆分后 bbox 高度统一使用 max_height

`translation_service.py` 第411-419行，拆分合并块时：

```python
new_bbox = (original_bbox[0], original_bbox[1], 
            original_bbox[0] + max_width, 
            original_bbox[1] + max_height)
```

每个拆分块的 bbox 高度都被设为 `max_height`（合并组中最大单块高度）。例如：
- 块A原始高度 12pt，块B原始高度 20pt，块C原始高度 15pt
- 合并后 `max_height = 20`
- 拆分后块A的 bbox 高度变为 20pt，向下扩展 8pt，侵入块B的视觉区域

这导致：
1. 块A的白色背景矩形向下扩展，可能覆盖块B的文本
2. 块A的文本在更大的 bbox 中渲染，可能溢出原始视觉区域
3. 块B的白色背景矩形绘制时，覆盖块A底部溢出的文本

### 问题2：PDF 生成器前两次尝试使用放大字体

`pdf_generator.py` 第272-274行：

```python
reduction_factor = (attempt - 3) * 0.1
adjusted_font_size = original_font_size * (1 - reduction_factor)
```

- 尝试1: `reduction_factor = -0.2` → `adjusted_font_size = original * 1.2`（放大20%）
- 尝试2: `reduction_factor = -0.1` → `adjusted_font_size = original * 1.1`（放大10%）
- 尝试3: `reduction_factor = 0` → `adjusted_font_size = original * 1.0`（原始大小）

当 bbox 被 max_height 扩展后，文本在更大的 bbox 中以放大字体渲染，`insert_textbox` 返回成功（文本确实放得下），但文本实际溢出了原始块的视觉区域。

### 用户报告的具体症状

1. **"统的全面概述，为你构建复杂LLM应用提供直觉和工具"只显示了2/3**：该块的 bbox 被 max_height 扩展，文本以放大字体渲染成功，但下一块的白色背景覆盖了该块底部1/3的文本
2. **"您可以利用这些资源来提升或发展您的先决技能。"前半段被下一段落挡住**：该块的 bbox 向下扩展，下一块的白色背景矩形（带 bg_padding）覆盖了该块底部的文本

## What Changes

- **修复合并块拆分后的 bbox 高度**：每个拆分块使用自身的原始 bbox 高度，而非统一的 max_height
- **修复 PDF 生成器字体大小计算**：前两次尝试不再使用放大字体，从原始字体大小开始

## Impact

- Affected code: `services/translation_service.py` 第411-419行, `modules/pdf_generator.py` 第272-274行
- 行为变更：拆分块使用原始 bbox 高度，PDF 渲染从原始字体大小开始
- 影响范围：所有使用语义合并的翻译流程

## ADDED Requirements

### Requirement: 合并块拆分后使用原始 bbox 高度

系统 SHALL 在拆分合并块时，每个拆分块使用自身的原始 bbox 高度，而非统一的 max_height。

#### Scenario: 拆分块保留原始高度

- **WHEN** 合并块被拆分为多个独立块
- **AND** 各原始块的高度不同
- **THEN** 每个拆分块的 bbox 高度使用该块自身的原始高度
- **AND** 拆分块的 bbox 宽度仍使用 max_width（保持当前行为，宽度扩展不会导致垂直遮挡）

#### Scenario: 拆分块不侵入相邻块视觉区域

- **WHEN** 拆分后的块按原始位置渲染
- **THEN** 每个块的 bbox 不向下扩展到下一块的区域

### Requirement: PDF 生成器从原始字体大小开始渲染

系统 SHALL 在 PDF 生成器的文本渲染尝试中，从原始字体大小开始，而非放大字体。

#### Scenario: 首次渲染使用原始字体大小

- **WHEN** PDF 生成器首次尝试渲染翻译文本
- **THEN** 使用原始字体大小（`adjusted_font_size = original_font_size`）

#### Scenario: 溢出时逐步缩小字体

- **WHEN** 首次渲染文本溢出
- **THEN** 逐步缩小字体大小（0.9x, 0.8x, 0.7x）
- **AND** 不使用放大字体

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
