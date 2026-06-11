# Tasks

- [ ] Task 1: 回退 `extract_table_cells_by_bbox` 方案，恢复使用 `table.extract()`
  - [ ] SubTask 1.1: 在 `extract_tables_by_pymupdf` 中将 `data = extract_table_cells_by_bbox(page, table)` 改回 `data = table.extract()`
  - [ ] SubTask 1.2: 保留 `page_table_cells` 的收集逻辑（改用 `table.cells` 直接获取单元格 bbox）
  - [ ] SubTask 1.3: 删除或标记废弃 `extract_table_cells_by_bbox` 函数

- [ ] Task 2: 实现 `separate_table_caption_and_footnote` 后处理函数
  - [ ] SubTask 2.1: 在 `table_processor.py` 中新增 `separate_table_caption_and_footnote(data, table_bbox)` 函数
  - [ ] SubTask 2.2: 遍历最后一行（和第一行）的每个单元格文本，使用正则匹配 "Table/Figure\s+\d+[\.\:]" 模式
  - [ ] SubTask 2.3: 定位标题文本在单元格文本中的起始位置，将标题及之后的所有文本分离
  - [ ] SubTask 2.4: 对跨单元格的标题文本进行合并（标题可能分散在多个单元格中）
  - [ ] SubTask 2.5: 如果分离后某行所有单元格为空/None，从 data 中移除该行
  - [ ] SubTask 2.6: 返回 `(cleaned_data, separated_texts)`，separated_texts 包含分离出的文本列表

- [ ] Task 3: 在 `extract_tables_by_pymupdf` 中集成后处理并扩展返回值
  - [ ] SubTask 3.1: 在 `table.extract()` 后调用 `separate_table_caption_and_footnote`
  - [ ] SubTask 3.2: 收集所有表格的 separated_texts，构建 `separated_text_blocks` 列表（包含 page_num, text, bbox 信息）
  - [ ] SubTask 3.3: 修改返回值为 `(pdf_tables, page_tables, page_table_cells, separated_text_blocks)`

- [ ] Task 4: 在 `pdf_extractor.py` 中集成分离的文本块
  - [ ] SubTask 4.1: 更新调用 `extract_tables_by_pymupdf` 的代码，接收新的四元组返回值
  - [ ] SubTask 4.2: 将 `separated_text_blocks` 转换为 TextBlock 对象，加入 text_blocks 列表
  - [ ] SubTask 4.3: camelot 分支返回空的 `separated_text_blocks`

- [ ] Task 5: 更新测试文件
  - [ ] SubTask 5.1: 更新 `test_pymupdf_table_extraction.py` 适配新的四元组返回值

- [ ] Task 6: 添加诊断日志
  - [ ] SubTask 6.1: 记录检测到的表格标题/脚注文本及其原始单元格位置
  - [ ] SubTask 6.2: 记录分离后的单元格文本和分离出的文本块信息

- [ ] Task 7: 验证修复效果
  - [ ] SubTask 7.1: 对包含 Table 5 的 PDF 运行程序，检查日志中表格标题分离的记录
  - [ ] SubTask 7.2: 检查 PDF 输出中 "Table 5. An example of role prompting" 和 "The above example shows..." 是否在表格下方正确位置翻译和渲染
  - [ ] SubTask 7.3: 检查其他页面的表格是否正常（无回归）

# Task Dependencies

- Task 2 依赖 Task 1（需要先回退无效方案）
- Task 3 依赖 Task 2（需要后处理函数）
- Task 4 依赖 Task 3（需要新的返回值）
- Task 5 依赖 Task 3（需要新的返回值格式）
- Task 6 依赖 Task 2（在实现逻辑时同步添加日志）
- Task 7 依赖 Task 1-6（需要所有代码修改完成后端到端验证）
