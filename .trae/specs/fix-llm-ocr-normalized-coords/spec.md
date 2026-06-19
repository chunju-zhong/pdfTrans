# 修复 DeepSeek-OCR 归一化坐标转换 Spec

## Why

DeepSeek-OCR 模型返回的 `<|det|>` bbox 坐标是**归一化坐标**（0-999 范围），不是像素坐标。当前代码将其当作像素坐标直接乘以 scale 转换为 PDF 点坐标，导致所有文本块位置严重偏移。例如 "Lesson:" 的 OCR bbox [700,422,776,461] 被错误转换为 (336.0, 202.5)，正确转换应为 (504.5, 171.1)，实际位置为 (505.3, 169.2)。

## What Changes

- 修改 `llm_extractor.py` 中的 `_pixel_to_pdf_coords` 方法，增加归一化坐标（0-999）到像素坐标的转换步骤
- 转换流程：归一化坐标 → 像素坐标 → PDF 点坐标

## Impact

- Affected code: `modules/ocr/llm_extractor.py`（`_pixel_to_pdf_coords` 方法）
- Affected specs: `fix-llm-ocr-coord-and-text`（坐标转换逻辑变更）
- **此修复同时解决了之前的三个渲染问题**（位置偏移、原文露出、文本不可见），因为根因都是坐标转换错误

## ADDED Requirements

### Requirement: DeepSeek-OCR 归一化坐标转换

LLM OCR 提取器 SHALL 将 DeepSeek-OCR 返回的 `<|det|>` bbox 坐标识别为归一化坐标（0-999 范围），并先转换为像素坐标再转换为 PDF 点坐标。

转换公式：
```
pixel_x = normalized_x / 999 * img_width_px
pixel_y = normalized_y / 999 * img_height_px
pdf_x = pixel_x * (page_width_pts / img_width_px)
pdf_y = pixel_y * (page_height_pts / img_height_px)
```

简化为：
```
pdf_x = normalized_x / 999 * page_width_pts
pdf_y = normalized_y / 999 * page_height_pts
```

#### Scenario: "Lesson:" 坐标转换

- **WHEN** DeepSeek-OCR 返回 sub_title bbox [700, 422, 776, 461]，页面 720x405pt，图像 1500x844px
- **THEN** 归一化转换：x0 = 700/999*720 = 504.5, y0 = 422/999*405 = 171.1, x1 = 776/999*720 = 559.3, y1 = 461/999*405 = 186.9
- **AND** 实际 PDF 位置 (505.3, 169.2, 559.8, 187.2)，误差 < 2pt

#### Scenario: 标题坐标转换

- **WHEN** DeepSeek-OCR 返回 title bbox [54, 25, 942, 88]
- **THEN** 归一化转换：x0 = 54/999*720 = 38.9, y0 = 25/999*405 = 10.1, x1 = 942/999*720 = 678.9, y1 = 88/999*405 = 35.7
- **AND** 实际标题文本延伸到 x=676.9，误差 < 2pt

#### Scenario: 图像坐标转换

- **WHEN** DeepSeek-OCR 返回 image bbox [18, 152, 678, 915]
- **THEN** 归一化转换：x0 = 18/999*720 = 13.0, y0 = 152/999*405 = 61.6, x1 = 678/999*720 = 488.7, y1 = 915/999*405 = 371.0

## MODIFIED Requirements

### Requirement: LLM OCR 坐标转换（原 fix-llm-ocr-coord-and-text）

LLM OCR 提取器 SHALL 使用归一化坐标转换方法，将 DeepSeek-OCR 返回的 0-999 范围坐标转换为 PDF 点坐标。

原方法：`pdf_coord = pixel_coord * (page_size / img_size)`
新方法：`pdf_coord = normalized_coord / 999 * page_size`

此修改应用于 `_pixel_to_pdf_coords` 方法，当检测到 DeepSeek-OCR 的 `<|ref|>` 标签格式时使用归一化转换。

### Requirement: 区分归一化坐标和像素坐标

`_pixel_to_pdf_coords` 方法 SHALL 根据调用上下文区分归一化坐标和像素坐标：
- DeepSeek-OCR `<|ref|>` 标签格式返回的坐标 → 归一化坐标（0-999）
- 其他 OCR 引擎返回的坐标 → 像素坐标

实现方式：添加 `is_normalized` 参数到 `_pixel_to_pdf_coords`，默认为 False。在 `_parse_ref_tags_response` 中调用时传入 `is_normalized=True`。
