# Tasks

- [x] Task 1: 修复 `_extract_text_blocks` 中 `Rect.intersect()` 原地修改 bug
  - [x] SubTask 1.1: `if current_page_table_cells:` 分支中 `block_rect & cell_rect`
  - [x] SubTask 1.2: `elif current_page_tables:` 分支中 `block_rect & table_rect`
  - [x] SubTask 1.3: 空列表回退的表格整体 bbox 检测中 `block_rect & table_rect`

- [x] Task 2: 修复 `pdf_extractor.py` 中其他 `intersect()` 调用（行452、463）
  - [x] SubTask 2.1: block_info_rect 循环中的 intersect 改为 &

- [x] Task 3: 修复 `style_analyzer.py` 中的 `intersect()` 调用（行63、79）
  - [x] SubTask 3.1: dict_rect 循环中的 intersect 改为 &

- [x] Task 4: 清理诊断日志
  - [x] SubTask 4.1: 移除 `pdf_extractor.py` 中所有 `[DIAG]` 日志
  - [x] SubTask 4.2: 移除 `table_processor.py` 中所有 `[DIAG]` 日志，保留有价值的 debug 日志

- [x] Task 5: 语法检查通过

# Task Dependencies

- Task 2, 3, 4 可并行
- Task 5 依赖 Task 1-4
