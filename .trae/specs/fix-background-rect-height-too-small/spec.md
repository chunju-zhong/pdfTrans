# 修复 OCR 模式覆盖原文白色背景高度偏小 Spec

## Why
OCR 模式下，PaddleOCR 版面分析返回的 bbox 是版面区域的紧密边界框，不含行间距（leading），导致白色背景无法完全覆盖原文——原文文字上下边缘会露出。非 OCR 模式下 PyMuPDF `get_text("blocks")` 返回的 bbox 包含完整文本块区域（含行间距），所以没有此问题。

## What Changes
- 在 `pdf_generator.py` 绘制白色背景时，基于 `font_size` 向上下扩展背景矩形
- 背景扩展与文本插入区域分离：背景矩形可大于文本插入矩形
- 修复语义合并时 `max_height` 取最大值而非累加的问题（加剧 OCR 模式下背景偏小）

## Impact
- Affected code: `modules/pdf_generator.py`, `utils/text_processing.py`
- Affected specs: 无

## ADDED Requirements

### Requirement: 白色背景上下扩展
绘制覆盖原文的白色背景时，SHALL 基于 `font_size` 向上下扩展背景矩形，确保完全覆盖原文（包括行间距区域）。

#### Scenario: OCR 模式单行文本背景扩展
- **WHEN** OCR 模式下绘制单行文本的白色背景
- **THEN** 背景矩形上下各扩展 `font_size * 0.3` 的 padding
- **AND** 文本仍使用原始 `block_bbox` 插入，不受背景扩展影响

#### Scenario: OCR 模式多行文本背景扩展
- **WHEN** OCR 模式下绘制多行文本的白色背景
- **THEN** 背景矩形上下各扩展 `font_size * 0.3` 的 padding
- **AND** 背景矩形不超出页面边界（clamp 到页面范围内）

#### Scenario: 非 OCR 模式不受影响
- **WHEN** 非 OCR 模式下绘制白色背景
- **THEN** 同样应用背景扩展逻辑（统一处理，不区分模式）

#### Scenario: 背景扩展与文本插入分离
- **WHEN** 白色背景矩形被扩展
- **THEN** 文本插入仍使用原始 `block_bbox`（未扩展的矩形）
- **AND** 文本溢出时的文本框调整仍基于原始 `block_bbox`

### Requirement: 语义合并时高度累加
语义合并多个文本块时，`max_height` SHALL 累加各子块高度和行间距，而非仅取最大值。此问题在 OCR 模式下尤为明显，因为 OCR bbox 本身就偏紧，合并后取最大值进一步缩小了覆盖区域。

#### Scenario: 多个子块合并
- **WHEN** 多个垂直相邻的文本块被合并为一个语义块
- **THEN** `max_height` = 第一个子块 y0 到最后一个子块 y1 的距离
- **AND** 合并后的 `block_bbox` 高度能覆盖所有子块的原始区域

#### Scenario: 单个子块
- **WHEN** 语义块只包含一个文本块
- **THEN** `max_height` 保持为该块的原始高度，无变化

## MODIFIED Requirements

### Requirement: pdf_generator.py 绘制背景逻辑
将 `page.draw_rect(rect, ...)` 中的 `rect` 从直接使用 `block_bbox` 改为扩展后的背景矩形。

修改前：
```python
rect = fitz.Rect(block_bbox[0], block_bbox[1], block_bbox[2], block_bbox[3])
page.draw_rect(rect, color=(1, 1, 1), fill=True, width=0)
```

修改后：
```python
rect = fitz.Rect(block_bbox[0], block_bbox[1], block_bbox[2], block_bbox[3])
bg_padding = original_font_size * 0.3
bg_rect = fitz.Rect(
    rect.x0,
    max(rect.y0 - bg_padding, 0),
    rect.x1,
    min(rect.y1 + bg_padding, page.rect.height)
)
page.draw_rect(bg_rect, color=(1, 1, 1), fill=True, width=0)
```

### Requirement: text_processing.py 合并高度计算
将 `max_height = max(current_merged.max_height, curr_height)` 改为基于第一个子块 y0 到当前子块 y1 的累加。

修改前：
```python
current_merged.max_height = max(current_merged.max_height, curr_height)
```

修改后：
```python
current_merged.max_height = curr_bbox[3] - first_bbox[1]
```

## REMOVED Requirements

无
