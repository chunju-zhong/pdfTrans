# Tasks

- [ ] Task 1: 在 table_processor.py 中补充基于 data 的 None 分布的 span 检测
  - [ ] SubTask 1.1: 当 span_map 为空但 data 中有 None 时，构建虚拟 bbox 矩阵（None 位置保持 None，非 None 位置用占位 bbox）
  - [ ] SubTask 1.2: 调用 compute_span_from_none_positions 计算补充 span_map
  - [ ] SubTask 1.3: 将补充的 span 设置到 PdfCell 的 row_span/col_span，并标记被合并位置为 None

- [ ] Task 2: 验证
  - [ ] SubTask 2.1: 语法检查通过
  - [ ] SubTask 2.2: 运行程序验证第22页表格的合并单元格被正确检测

# Task Dependencies

- Task 2 依赖 Task 1
