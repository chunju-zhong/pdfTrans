# Tasks

- [x] Task 1: 将表格 bbox 加入 processed_pixel_bboxes，防止表格内 textline 被重复捕获为 supplement TextBlock
  - [x] SubTask 1.1: 在 `_process_page_layout()` 第868-869行，当 `label == 'table'` 时，将 `(x1, y1, x2, y2)` 加入 `processed_pixel_bboxes`
  - [x] SubTask 1.2: 确保表格提取失败时也加入 bbox（在表格处理的所有分支中都加入）

- [x] Task 2: 将 `_estimate_text_display_width()` 从 `llm_extractor.py` 提取到 `modules/extractors/coordinate_utils.py`
  - [x] SubTask 2.1: 在 `coordinate_utils.py` 中添加 `estimate_text_display_width()` 函数
  - [x] SubTask 2.2: 在 `llm_extractor.py` 中改为从 `coordinate_utils` 导入，删除本地定义

- [x] Task 3: 在 PaddleOCR `_compute_table_grid()` 中计算并设置 `estimated_lines`
  - [x] SubTask 3.1: 从 textline bbox 高度估算字体大小（取中位数），无 textline 时默认 9.0
  - [x] SubTask 3.2: 在列宽计算完成后，对每个有文本的单元格计算 `estimated_lines = max(1, ceil(display_width / span_width))`
  - [x] SubTask 3.3: 将 `estimated_lines` 写入 `cell.estimated_lines`，空单元格设为 0

- [x] Task 4: 验证修复效果
  - [x] SubTask 4.1: 导入测试通过，`estimate_text_display_width` 正确提取到共享模块
  - [x] SubTask 4.2: `_compute_table_grid` 包含 `estimated_lines` 计算逻辑
  - [x] SubTask 4.3: `processed_pixel_bboxes.append` 在表格处理分支中存在

# Task Dependencies
- Task 3 依赖 Task 2（需要共享的 `estimate_text_display_width`）
- Task 4 依赖 Task 1 + Task 3
- Task 1 和 Task 2/3 可并行
