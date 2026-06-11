# Tasks

- [x] Task 1: 修改 `_compute_table_grid` 添加缩放逻辑（网格填满表格 bbox）
  - [x] SubTask 1.1: 在 row_heights/col_widths 计算后添加按比例缩放
  - [x] SubTask 1.2: 语法检查 + 单元测试

- [x] Task 2: 修改 `_draw_translated_table` 改用统一网格线画法
  - [x] SubTask 2.1: 删除单元格循环内的边框绘制代码
  - [x] SubTask 2.2: 在单元格循环后添加统一网格线绘制（外框 `draw_rect` + 内部横线/竖线 `draw_line`）
  - [x] SubTask 2.3: 语法检查

- [ ] Task 3: 运行程序验证（需要用户提供测试 PDF）
  - [ ] SubTask 3.1: 运行程序检查表格线条（外框、横线、竖线）是否完整
  - [ ] SubTask 3.2: 检查原表格是否被完全覆盖

# Task Dependencies

Task 2 依赖 Task 1