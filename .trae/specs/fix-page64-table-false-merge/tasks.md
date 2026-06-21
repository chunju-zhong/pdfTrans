# Tasks

- [ ] Task 1: 在 `compute_span_from_none_positions` 中增加几何验证
  - [ ] SubTask 1.1: 计算推断 span 覆盖区域的几何尺寸（基于 bbox_matrix 中各行列的 bbox 宽高）
  - [ ] SubTask 1.2: 比较起始单元格 bbox 与覆盖区域尺寸，覆盖率 < 80% 则判定为无效 span
  - [ ] SubTask 1.3: 仅将通过几何验证的 span 加入 span_map 返回值
  - [ ] SubTask 1.4: 在验证失败时记录 DEBUG 日志（单元格坐标、推断 span、bbox 尺寸、覆盖区域尺寸、失败原因）

- [ ] Task 2: 在 `table_processor.py` 中为非合并的 None 位置创建空 PdfCell
  - [ ] SubTask 2.1: 构建 span 覆盖位置集合（从有效 span_map 计算所有被合并覆盖的坐标）
  - [ ] SubTask 2.2: 遍历 data 时，对 bbox_matrix 中为 None 但不在覆盖集合中的位置，使用均匀分割计算 bbox 并创建 text="" 的 PdfCell
  - [ ] SubTask 2.3: 对在覆盖集合中的 None 位置，保持跳过逻辑不变

- [ ] Task 3: 验证
  - [ ] SubTask 3.1: 语法检查通过
  - [ ] SubTask 3.2: 运行程序验证第64页表格不再误合并
  - [ ] SubTask 3.3: 验证真正有合并单元格的表格仍然正确合并

# Task Dependencies
- Task 2 依赖 Task 1（需要有效 span_map 来区分合并 None 和空单元格 None）
- Task 3 依赖 Task 1 和 Task 2
