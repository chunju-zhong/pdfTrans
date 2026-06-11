# Tasks

- [x] Task 1: 新增 `_compute_span_from_none_positions` 函数
  - [x] 在 `modules/extractors/coordinate_utils.py` 中新增函数
  - [x] 从 `bbox_matrix` 中 None 的位置推断合并单元格的 row_span/col_span
  - [x] 返回 `{(row_idx, col_idx): (row_span, col_span)}` 字典

- [x] Task 2: 替换 table_processor.py 中的阈值检测为 None 位置推断
  - [x] 移除 `uniform_row_height` / `uniform_col_width` 计算和 1.5 倍阈值检测逻辑
  - [x] 调用 `_compute_span_from_none_positions` 获取 span_map
  - [x] 使用 `span_map.get((row_idx, col_idx), (1, 1))` 替代原来的阈值检测
  - [x] 保留合并覆盖位置设为 None 的逻辑

- [x] Task 3: 验证
  - [x] 编译检查
  - [x] 运行相关测试

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 1 and Task 2
