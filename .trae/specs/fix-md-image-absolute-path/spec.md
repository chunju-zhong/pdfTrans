# Fix Markdown Image Absolute Path Spec

## Why
OCR识别翻译生成的 Markdown 文件中，图片引用使用了指向工具内部临时目录 `temp_images/` 的绝对路径（如 `/Users/chunju/work/pdfTrans/temp_images/ocr_img_p36_1.png`），导致下载或分享后的 Markdown 无法正常显示图片。

## Root Cause
`paddle_extractor.py` 在 OCR 提取完成后会清理 `temp_images/` 目录，但此时 Markdown 生成器尚未执行图片复制操作。当 `markdown_generator.py` 的 `_copy_images_to_output()` 尝试将图片复制到输出目录时，源文件已不存在，只能保留原始的绝对路径。

## What Changes
- **paddle_extractor.py**: 删除 OCR 提取完成后的 `temp_images/` 目录清理逻辑
- **translation_service.py**: 在翻译服务层统一管理 `temp_images/` 的清理时机，确保所有输出文件生成完成后才清理
- **translation_service.py**: 新增对 `temp_images/` 的引用传递，确保清理能正确执行

## Impact
- Affected specs: Markdown 输出生成流程
- Affected code: 
  - `modules/ocr/paddle_extractor.py` — 删除 temp_images 清理
  - `services/translation_service.py` — 统一管理 temp_images 清理时机

## ADDED Requirements
### Requirement: Markdown 图片路径为相对路径
The system SHALL ensure that the generated markdown file uses relative paths for images (e.g., `images_xxx/ocr_img_p36_1.png`) instead of absolute paths to the internal temp directory.

#### Scenario: OCR 模式生成 Markdown
- **WHEN** user translates a PDF in OCR mode with markdown output format
- **THEN** the generated markdown file shall contain relative image paths that work within the downloaded ZIP package

### Requirement: 图片在输出文件生成完成后才清理
The system SHALL ensure that temp images are only cleaned up after ALL output files (PDF, DOCX, MD) have been fully generated.

#### Scenario: 多格式输出
- **WHEN** user selects multiple output formats (e.g., pdf + docx + md)
- **THEN** all output files shall be generated successfully with correct images
- **AND** temp images shall only be cleaned up after all outputs are complete

## MODIFIED Requirements
### Requirement: OCR Extractor 临时目录清理
The paddle_extractor SHALL NOT clean up the temp_images directory after extraction. This responsibility is moved to the translation service layer.

## REMOVED Requirements
None.
