# Tasks

- [x] Task 1: 修复 `_pixel_to_pdf_coords` 像素坐标 Y 轴翻转
  - [x] 在 `is_normalized=False` 分支添加 Y 轴翻转：`pdf_y1 = (img_height - y2) * scale_y, pdf_y2 = (img_height - y1) * scale_y`
  - [x] `paddle_extractor.py` 中已存在正确的 Y 轴翻转，无需更新
- [x] Task 2: 修复 `_pixel_to_pdf_coords` 归一化坐标 Y 轴翻转
  - [x] 在 `is_normalized=True` 分支添加 Y 轴翻转：`pdf_y1 = (999 - y2) / 999 * page_height, pdf_y2 = (999 - y1) / 999 * page_height`
- [ ] Task 3: 添加坐标转换调试日志
  - [ ] 在 `_pixel_to_pdf_coords` 中添加 DEBUG 日志记录转换前后坐标
- [x] Task 4: 验证修复
  - [x] 使用第6页数据验证：像素 bbox [176, 85, 1234, 195] → PDF y≈185~211 ✓

# Task Dependencies
- Task 1 and Task 2 are independent (can be done in parallel)
- Task 4 depends on Task 1 + Task 2