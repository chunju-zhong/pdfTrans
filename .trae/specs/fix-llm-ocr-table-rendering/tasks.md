# Tasks

- [x] Task 1: 修复 `_parse_html_table` - 添加 table bbox 参数，基于 bbox 和 rowspan/colspan 计算每个单元格的真实坐标
  - [x] 修改 `_parse_html_table` 方法签名，增加 `table_bbox` 参数
  - [x] 在创建 PdfCell 时，根据 table bbox、行数、列数、rowspan、colspan 计算每个单元格的 bbox
  - [x] 返回 cells 的同时返回计算的 row_heights 和 col_widths

- [x] Task 2: 修复 `_parse_json_response` - 使用新的 `_parse_html_table` 结果构建完整的 PdfTable
  - [x] 调用 `_parse_html_table(html, table_bbox=pdf_bbox)` 传入表格级 bbox
  - [x] 将计算得到的 row_heights 和 col_widths 传入 PdfTable 构造函数
  - [x] 添加日志输出计算结果

- [x] Task 3: 为 `_parse_ref_tags_response` 和 `_parse_markdown_response` 添加 HTML 表格检测
  - [x] 编写 `_extract_tables_from_text` 辅助方法，用正则从文本中提取 `<table>...</table>` HTML
  - [x] 在 `_parse_ref_tags_response` 中调用表格检测，将检测到的表格加入返回值
  - [x] 在 `_parse_markdown_response` 中调用表格检测（Markdown 响应可能包含 HTML 表格片段）
  - [x] 检测到的表格使用页面默认 bbox（或全页 bbox 的某个比例区域）

- [x] Task 4: 验证 PDF 表格绘制效果
  - [x] 确认 JSON 路径的表格有正确的 row_heights/col_widths 和 cell bbox
  - [x] 确认非 JSON 路径能提取到表格数据
  - [x] 运行现有测试确认不引入回归（80 passed + 7 table tests passed）

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] 可与 [Task 1] 并行执行
- [Task 4] depends on [Task 1, Task 2, Task 3]
