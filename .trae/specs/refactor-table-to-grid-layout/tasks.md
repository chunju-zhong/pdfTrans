# Tasks

- [x] Task 1: 实现 `_compute_table_grid` 方法替换 `_compute_cell_bboxes`
  - [x] SubTask 1.1: 新增 `_compute_table_grid` 静态方法，按行列区域分组 textline，计算每行统一行高和每列统一列宽
  - [x] SubTask 1.2: 基于累积行高/列宽为每个单元格计算网格 bbox，更新 `cell.bbox`/`cell.width`/`cell.height`
  - [x] SubTask 1.3: 删除旧的 `_compute_cell_bboxes` 方法

- [x] Task 2: 修改表格处理调用逻辑
  - [x] SubTask 2.1: 修改第 615-632 行，调用 `_compute_table_grid` 获取 `cells, row_heights_px, col_widths_px`
  - [x] SubTask 2.2: 保持已有的像素→PDF 坐标转换循环（`cell.bbox` 转换）
  - [x] SubTask 2.3: 将 `row_heights_px` 和 `col_widths_px` 转换为 PDF 点单位后设置到 `PdfTable.row_heights` 和 `PdfTable.col_widths`

- [x] Task 3: 验证
  - [x] SubTask 3.1: 语法检查
  - [x] SubTask 3.2: 运行单元测试（3/3 通过，165 个全量测试通过）
  - [ ] SubTask 3.3: 运行程序验证表格字体一致性和线条整齐（需要用户提供测试 PDF）

# Task Dependencies

Task 2 依赖 Task 1
Task 3 依赖 Task 1, Task 2