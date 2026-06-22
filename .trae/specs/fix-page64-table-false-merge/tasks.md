# Tasks

- [ ] Task 1: 在 `coordinate_utils.py` 中新增工具函数
  - [ ] SubTask 1.1: `detect_incomplete_table(table, page, row_threshold=2, x_overlap_threshold=0.5)` — 判断表格是否可能不完整（行数≤阈值且下方有对齐文本块）
  - [ ] SubTask 1.2: `find_data_row_region(table_bbox, page, gap_threshold=25, width_tolerance=50)` — 扫描表格下方文本块，确定数据行区域边界
  - [ ] SubTask 1.3: `compute_row_boundaries(text_blocks, row_group_tolerance=5)` — 将文本块按y0分组，计算每行边界
  - [ ] SubTask 1.4: `extract_data_rows_by_col_bounds(page, col_boundaries, row_boundaries, table_bbox)` — 使用列边界+行边界，通过字符级重叠分配提取数据行单元格

- [ ] Task 2: 在 `table_processor.py` 中集成不完整表格扩展逻辑
  - [ ] SubTask 2.1: 在 `extract_tables_by_pymupdf` 的表格处理循环中，对每个表格调用 `detect_incomplete_table`
  - [ ] SubTask 2.2: 对不完整表格，调用 `find_data_row_region` 和 `compute_row_boundaries` 确定数据行
  - [ ] SubTask 2.3: 调用 `extract_data_rows_by_col_bounds` 提取数据行单元格内容
  - [ ] SubTask 2.4: 合并表头行和数据行，构建完整的 `data`、`rows_data`、`bbox_matrix`
  - [ ] SubTask 2.5: 调用 `compute_span_from_none_positions` 推断合并单元格
  - [ ] SubTask 2.6: 创建 PdfCell 对象，构建 cell_matrix，计算行高列宽
  - [ ] SubTask 2.7: 创建 PdfTable 对象，替换原始不完整表格
  - [ ] SubTask 2.8: 更新 `page_table_cells` 和 `page_tables` 返回值
  - [ ] SubTask 2.9: 异常处理：扩展失败时回退到原始表格，记录 WARNING 日志

- [ ] Task 3: 验证
  - [ ] SubTask 3.1: 语法检查通过
  - [ ] SubTask 3.2: 运行程序验证第64页表格被正确扩展（1行→9行，包含所有数据行）
  - [ ] SubTask 3.3: 验证数据行文本块被 is_table_text 正确过滤，不再作为普通文本渲染
  - [ ] SubTask 3.4: 验证其他页面的表格不受影响（行数≥3的表格不触发扩展）
  - [ ] SubTask 3.5: 验证真正有合并单元格的表格仍然正确合并

# Task Dependencies
- Task 2 依赖 Task 1（需要工具函数）
- Task 3 依赖 Task 1-2
