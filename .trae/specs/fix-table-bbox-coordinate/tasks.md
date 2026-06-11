# Tasks

- [x] Task 1: 修复表格 bbox 坐标转换
  - [x] SubTask 1.1: 在 `paddle_extractor.py` 的表格处理代码中，将手动 Y 翻转改为调用 `self._pixel_to_pdf_coords(bbox, page_info)`
  - [x] SubTask 1.2: 添加坐标转换诊断日志（像素坐标和 PDF 坐标）
- [ ] Task 2: 验证表格位置（需要运行程序并检查 `[TABLE_DIAG]` 日志和 PDF 输出）
  - [ ] SubTask 2.1: 运行 OCR 提取，检查 `[TABLE_DIAG]` 日志中的坐标值
  - [ ] SubTask 2.2: 生成 PDF 输出，检查表格是否覆盖原表格

# Task Dependencies

- Task 2 依赖 Task 1
