# Tasks

- [ ] Task 1: 在 `_parse_html_table` 中增加 PaddleOCR 原始 HTML 调试日志
  - [ ] SubTask 1.1: 在 `_parse_html_table` 方法入口处记录原始 HTML 前500字符到 DEBUG 日志
  - [ ] SubTask 1.2: 在 `_TableHtmlParser` 解析完成后记录每行的单元格数量

- [ ] Task 2: 增加行单元格数与表头列数的一致性验证
  - [ ] SubTask 2.1: 在 `_parse_html_table` 中，解析完成后检查每行的 `<td>` 数量是否等于第一行（表头）的列数
  - [ ] SubTask 2.2: 如果不一致，记录 WARNING 日志，包含行号、实际单元格数、预期列数、该行解析结果

- [ ] Task 3: 利用 textline 位置信息分割被错误合并的单元格
  - [ ] SubTask 3.1: 在 `_parse_html_table` 或 `_expand_html_table` 中，当检测到某行单元格数不足时，获取该表格区域的 textline 信息
  - [ ] SubTask 3.2: 根据表头列的 x 坐标范围，将合并单元格中的 textline 按位置分配到正确的列
  - [ ] SubTask 3.3: 用分割后的文本创建多个 PdfCell 替换原始合并单元格
  - [ ] SubTask 3.4: 如果 textline 位置不足以分割，保留原始文本并记录 WARNING

- [ ] Task 4: 验证修复效果
  - [ ] SubTask 4.1: 重新处理第64页 PDF，确认 (5,0) 显示 "OpenWebText2"，(5,1) 显示 "Outbound Reddit链接" 的翻译
  - [ ] SubTask 4.2: 确认日志中出现 HTML 验证相关的 DEBUG/WARNING 信息

# Task Dependencies
- [Task 3] depends on [Task 1] and [Task 2]
- [Task 4] depends on [Task 3]
