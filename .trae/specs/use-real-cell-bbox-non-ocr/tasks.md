# Tasks

- [x] Task 1: 新增 `_build_bbox_matrix` 辅助函数，将 `extract_table_cells_by_bbox` 返回的 `rows_data` 转为行×列 bbox 矩阵
  - [x] SubTask 1.1: 在 `coordinate_utils.py` 中新增 `_build_bbox_matrix(rows_data, num_rows, num_cols)` 函数
  - [x] SubTask 1.2: 处理 `rows_data` 中行长度不一致的情况（短行用 None 填充）

- [x] Task 2: 新增 `calculate_row_heights_from_bboxes` 和 `calculate_col_widths_from_bboxes` 函数
  - [x] SubTask 2.1: `calculate_row_heights_from_bboxes(bbox_matrix)` — 从真实 bbox 推算行高（同行取最大 y1-y0）
  - [x] SubTask 2.2: `calculate_col_widths_from_bboxes(bbox_matrix, table_bbox)` — 从真实 bbox 推算列宽（合并单元格按跨列数等分分配，每列取最大值）

- [x] Task 3: 修改 `extract_tables_by_pymupdf` 使用真实单元格 bbox
  - [x] SubTask 3.1: 当 `table_cell_bboxes` 非空时，调用 `_build_bbox_matrix` 构建 bbox 矩阵
  - [x] SubTask 3.2: 用 bbox 矩阵中的真实 bbox 替代 `calculate_cell_bbox` 均匀分割
  - [x] SubTask 3.3: 用 `calculate_row_heights_from_bboxes` / `calculate_col_widths_from_bboxes` 替代原计算函数
  - [x] SubTask 3.4: 当 `table_cell_bboxes` 为空时，保持回退到均匀分割

- [x] Task 4: 验证
  - [x] SubTask 4.1: 语法检查
  - [x] SubTask 4.2: 运行现有单元测试（390 passed, 1 skipped）
  - [ ] SubTask 4.3: 运行程序验证非 OCR 模式表格精准还原（需用户提供测试 PDF）

# Task Dependencies

- Task 2 依赖 Task 1
- Task 3 依赖 Task 1, Task 2
- Task 4 依赖 Task 3
