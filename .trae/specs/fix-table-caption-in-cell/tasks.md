# Tasks

- [ ] Task 1: 实现 `separate_table_caption_and_footnote` 后处理函数
  - [ ] SubTask 1.1: 在 `table_processor.py` 中新增 `separate_table_caption_and_footnote(data, table_bbox)` 函数
  - [ ] SubTask 1.2: 遍历最后一行（和第一行）的每个单元格文本，使用正则匹配 "Table/Figure\s+\d+[\.\:]" 模式
  - [ ] SubTask 1.3: 定位标题文本在单元格文本中的起始位置，将标题及之后的所有文本分离
  - [ ] SubTask 1.4: 对跨单元格的标题文本进行合并（标题可能分散在多个单元格中，如 "OutputTable 5. An example" 中 "Output" 是单元格数据，"Table 5." 是标题开始）
  - [ ] SubTask 1.5: 如果分离后某行所有单元格为空/None，从 data 中移除该行
  - [ ] SubTask 1.6: 返回 `(cleaned_data, separated_texts)`，separated_texts 包含分离出的文本列表

- [ ] Task 2: 在 `extract_tables_by_pymupdf` 中集成后处理并扩展返回值
  - [ ] SubTask 2.1: 在 `extract_table_cells_by_bbox` 之后调用 `separate_table_caption_and_footnote`
  - [ ] SubTask 2.2: 收集所有表格的 separated_texts，构建 `separated_text_blocks` 列表（包含 page_num, text, bbox 信息）
  - [ ] SubTask 2.3: 修改返回值为 `(pdf_tables, page_tables, page_table_cells, separated_text_blocks)`

- [ ] Task 3: 在 `pdf_extractor.py` 中集成分离的文本块
  - [ ] SubTask 3.1: 更新调用 `extract_tables_by_pymupdf` 的代码，接收新的四元组返回值
  - [ ] SubTask 3.2: 将 `separated_text_blocks` 转换为 TextBlock 对象，加入 text_blocks 列表
  - [ ] SubTask 3.3: camelot 分支返回空的 `separated_text_blocks`

- [ ] Task 4: 更新测试文件
  - [ ] SubTask 4.1: 更新测试适配新的四元组返回值

- [ ] Task 5: 添加诊断日志
  - [ ] SubTask 5.1: 记录检测到的表格标题/脚注文本及其原始单元格位置
  - [ ] SubTask 5.2: 记录分离后的单元格文本和分离出的文本块信息

- [ ] Task 6: 验证
  - [ ] SubTask 6.1: 语法检查和单元测试
  - [ ] SubTask 6.2: 运行程序验证第22页表格标题分离效果（需用户提供测试 PDF）

# Task Dependencies

- Task 2 依赖 Task 1
- Task 3 依赖 Task 2
- Task 4 依赖 Task 2
- Task 5 依赖 Task 1
- Task 6 依赖 Task 1-5
