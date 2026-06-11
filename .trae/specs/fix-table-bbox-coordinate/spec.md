# 修复 OCR 表格 PDF 坐标转换错误 Spec

## Why

OCR 表格 bbox 转换为 PDF 坐标时，使用了与文本块不同的坐标转换逻辑。文本块使用 `_pixel_to_pdf_coords`（不做 Y 翻转），而表格代码手动进行了 Y 翻转，导致表格位置偏上，无法覆盖原表格。

## 根因分析

PP-StructureV3 的 `parsing_res_list` 返回的 bbox 已处于 PDF 兼容坐标系（原点在左上角但 Y 方向无需翻转即可直接缩放），因此：
- **文本块**：`_pixel_to_pdf_coords` 直接 `bbox * scale`，不翻转 Y → 位置正确
- **表格**：手动 `img_height_px - bbox[3]` 翻转 Y → 位置偏上偏移

以日志中表格 bbox `(76.13, 267.44, 516.74, 455.12)` 为例：
- 不翻转 Y: y≈133-228（正确位置，页面偏上部分）
- 翻转 Y: y≈564-658（错误位置，页面偏下部分）

## What Changes

- **统一使用 `_pixel_to_pdf_coords`**：将表格 bbox 转换从手动 Y 翻转改为调用 `self._pixel_to_pdf_coords(bbox, page_info)`
- **使用 `_table_res_list_parser` 获取表格 bbox**：如果 `from paddlex.inference.pipelines.table_recognition.result import SingleTableRecognitionResult` 可用，则直接从 `table_res` 的 `cell_box_list` 计算表格整体 bbox，避免依赖 `parsing_res_list` 的 `table` 标签

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`

## ADDED Requirements

### Requirement: 表格 bbox 使用统一坐标转换

系统在 OCR 提取表格时，必须使用 `_pixel_to_pdf_coords` 方法进行坐标转换，与文本块保持一致。

#### Scenario: 表格 bbox 转换
- **WHEN** 从 `parsing_res_list` 获取表格 bbox
- **THEN** 调用 `self._pixel_to_pdf_coords(bbox, page_info)` 转换坐标
- **AND** 不手动翻转 Y 坐标

### Requirement: 表格坐标诊断日志

系统在转换表格 bbox 后，应记录像素坐标和 PDF 坐标的值，便于诊断位置偏差。

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
