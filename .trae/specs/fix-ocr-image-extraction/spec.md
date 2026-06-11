# OCR 模式图片提取改进 Spec

## Why
OCR 模式下，步骤0 使用 PyMuPDF 提取嵌入图像对扫描件/图片PDF无效，应直接使用 PPStructureV3 版面分析检测到的图像区域作为唯一图像来源。

## What Changes
- **删除步骤0**：移除 `_extract_original_images` 方法及调用，OCR 模式下不再使用 PyMuPDF 提取嵌入图像
- **步骤4 成为唯一图像来源**：`all_images = chart_seal_images`（仅 PPStructureV3 裁剪的图像）

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`

## ADDED Requirements
无

## MODIFIED Requirements
无

## REMOVED Requirements

### Requirement: 步骤0 PyMuPDF 嵌入图像提取
**Reason**: OCR 模式下 PyMuPDF 提取嵌入图像对扫描件无效，PPStructureV3 版面分析+裁剪是更可靠的图像来源。
**Migration**: 删除 `_extract_original_images` 方法及其调用，`all_images` 直接等于 `chart_seal_images`。
