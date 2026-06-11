# Tasks

- [x] Task 1: PdfCell 新增 row_span 和 col_span 字段
  - [x] 在 `models/extraction.py` 的 `PdfCell.__init__` 中添加 `row_span=1, col_span=1` 参数
  - [x] 更新 `from_dict` 和 `to_dict` 方法支持新字段
  - [x] 确保所有创建 PdfCell 的位置兼容（默认值 1）

- [x] Task 2: _TableHtmlParser 解析 rowspan/colspan 并展开为二维矩阵
  - [x] 修改 `_TableHtmlParser.handle_starttag` 提取 `rowspan`/`colspan` 属性
  - [x] 修改 `handle_endtag` 存储 (text, rowspan, colspan) 元组
  - [x] 新增 `_expand_html_table` 静态方法，将稀疏行展开为完整二维矩阵（起始位置为 PdfCell，被合并位置为 None）
  - [x] 修改调用 `_TableHtmlParser` 的代码，使用 `_expand_html_table` 替代原来的简单二维列表

- [x] Task 3: _compute_table_grid 支持合并单元格 bbox 计算
  - [x] 修改 `_compute_table_grid`，遍历单元格时检查 `row_span`/`col_span`
  - [x] 合并单元格的 bbox 覆盖多行多列（使用 `sum(row_heights[row:row+span])` 和 `sum(col_widths[col:col+span])`）
  - [x] 被合并位置 (None) 跳过 bbox 设置

- [x] Task 4: _draw_translated_table 跳过被合并位置并优化网格线
  - [x] 单元格循环中，`cell is None` 时跳过背景和文本绘制
  - [x] 新增 `_compute_visible_segments` 辅助函数
  - [x] 构建遮挡信息表（h_line_blocked / v_line_blocked）
  - [x] 水平线绘制：按可见段绘制，跳过被合并单元格遮挡的段
  - [x] 垂直线绘制：同理按可见段绘制
  - [x] 合并单元格文本绘制：使用跨行跨列的 bbox，字体大小基于完整高度计算

- [x] Task 5: PyMuPDF 路径设置 row_span/col_span
  - [x] 在 `table_processor.py` 中，利用 `rows_data` 的 bbox 信息计算合并单元格的 span
  - [x] 被合并位置（`cell_bbox is None`）在 `cell_matrix` 中设为 `None`
  - [x] 起始位置的 `PdfCell` 设置正确的 `row_span`/`col_span`

- [x] Task 6: 验证与测试
  - [x] 运行现有单元测试确保无回归
  - [x] 检查语法和类型正确性

# Task Dependencies

- Task 2 depends on Task 1（PdfCell 需要先有 row_span/col_span 字段）
- Task 3 depends on Task 1 and Task 2（需要合并信息才能计算 bbox）
- Task 4 depends on Task 1 and Task 3（需要合并信息和正确的 bbox）
- Task 5 depends on Task 1（需要 PdfCell 有 span 字段）
- Task 6 depends on all previous tasks
