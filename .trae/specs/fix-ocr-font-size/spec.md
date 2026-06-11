# OCR 字体大小估算改进 Spec

## Why
PPStructureV3 返回的文本是按块（block）级别的，一个 block 可能包含多行文本但没有换行符，导致当前基于 `bbox_height / num_lines * 0.6` 的字体大小估算严重不准确（大量文本块被估算为上限值 20pt）。

## What Changes
- 使用 PPStructureV3 result 中的 `overall_ocr_res.rec_boxes` 获取 textline 级别的 bbox 高度来估算字体大小
- 使用 `LayoutBlock.num_of_lines` 和 `LayoutBlock.text_line_height` 作为辅助信息
- 移除当前基于换行符计数的估算算法
- 提高字体大小上限从 20pt 到 36pt

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`

## 深度分析

### 当前算法的问题

当前算法（第 383-386 行）：
```python
bbox_height = pdf_bbox[3] - pdf_bbox[1]
num_lines = max(1, text.strip().count('\n') + 1)
estimated_font_size = max(6, min(20, (bbox_height / num_lines) * 0.6))
```

**问题 1：PPStructureV3 的文本块没有换行符**

FONT_DEBUG 日志证据：几乎所有 `label=text` 的块都是 `font_size=20.00`（上限值），因为 `count('\n')` 永远为 0，`num_lines=1`。

**问题 2：0.6 系数不准确**

PDF 点坐标中的 bbox 高度与字体大小（pt）的关系取决于行间距，通常行间距是字体大小的 1.2-1.5 倍，因此系数应该是 `1 / 1.2 ≈ 0.83` 到 `1 / 1.5 ≈ 0.67`。

**问题 3：上限 20pt 太低**

文档标题通常使用 24-36pt 字体。

### PPStructureV3 result 对象中的 textline 信息

通过探索 PPStructureV3 的 result 对象，发现以下关键数据源：

**1. `overall_ocr_res`（OCRResult）**

| 属性 | 类型 | 说明 |
|------|------|------|
| `rec_boxes` | `list` | 每行文本的矩形框 `[x1,y1,x2,y2]`（像素坐标） |
| `rec_texts` | `list[str]` | 每行识别文字 |
| `rec_scores` | `list[float]` | 每行置信度 |

**2. `LayoutBlock` 的属性**

| 属性 | 类型 | 说明 |
|------|------|------|
| `num_of_lines` | `int` | 文本行数 |
| `text_line_height` | `float` | 平均文本行高度 |
| `text_line_width` | `float` | 平均文本行宽度 |

### 推荐方案：使用 `overall_ocr_res.rec_boxes` 估算字体大小

**核心思路**：`rec_boxes` 中每个 textline 的 bbox 高度直接对应单行文字的高度，可以准确估算字体大小。

具体步骤：
1. 从 `result["overall_ocr_res"]` 获取 `rec_boxes` 和 `rec_texts`
2. 对于每个 TEXT_LABELS 的 block，找到落在该 block bbox 范围内的 textline
3. 用这些 textline 的 bbox 高度（转换为 PDF 点坐标后）的平均值估算字体大小
4. 系数使用 0.75（考虑行间距约为字号的 1.33 倍）

**备选方案**：如果 `overall_ocr_res` 不可用或为空，回退到使用 `LayoutBlock.text_line_height`（如果该属性有值），或使用 `LayoutBlock.num_of_lines` 来计算行数。

## ADDED Requirements

### Requirement: 使用 textline bbox 高度估算字体大小
系统 SHALL 使用 PPStructureV3 result 中的 `overall_ocr_res.rec_boxes` 获取 textline 级别的 bbox 高度来估算字体大小。

#### Scenario: 通过 textline 高度估算字体大小
- **WHEN** PPStructureV3 返回一个文本块，`overall_ocr_res` 中有落在该 block bbox 范围内的 textline
- **THEN** 系统 SHALL 用这些 textline 的 bbox 高度平均值（转换为 PDF 点坐标后）* 0.75 估算字体大小

#### Scenario: overall_ocr_res 不可用
- **WHEN** `overall_ocr_res` 为空或不包含 `rec_boxes`
- **THEN** 系统 SHALL 回退到使用 `LayoutBlock.num_of_lines`（如果有值）或 `LayoutBlock.text_line_height` 来估算字体大小

#### Scenario: 所有回退方案均不可用
- **WHEN** textline 信息和 num_of_lines 均不可用
- **THEN** 系统 SHALL 使用当前算法（bbox_height * 0.75）作为最终回退

## MODIFIED Requirements

### Requirement: 字体大小上限
字体大小上限 SHALL 从 20pt 提高到 36pt，以覆盖标题等大字体场景。

## REMOVED Requirements
无
