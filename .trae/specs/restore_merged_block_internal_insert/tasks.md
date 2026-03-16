# 恢复合并块内部图表插入功能 - 任务列表

## 任务列表

- [ ] 任务1: 分析当前代码结构，理解现有图表位置处理逻辑
  - [ ] 分析 docx_generator.py 中 _process_page_elements 和相关方法
  - [ ] 分析 markdown_generator.py 中 _process_page_elements 和相关方法
  - [ ] 分析 _find_chart_position 和 _find_merged_block 方法

- [ ] 任务2: 修改 docx_generator.py 的 _process_page_elements 方法
  - [ ] 增加检测图表是否位于合并块内部的逻辑
  - [ ] 当图表位于合并块内部时，调用 _insert_element_in_text_block 方法
  - [ ] 保持现有在合并块之前/之后插入的逻辑作为回退

- [ ] 任务3: 修改 markdown_generator.py 的 _process_page_elements 方法（完整Markdown模式）
  - [ ] 增加检测图表是否位于合并块内部的逻辑
  - [ ] 创建 _insert_element_in_merged_block 辅助方法
  - [ ] 实现Markdown版本的拆分插入逻辑

- [ ] 任务4: 修改 markdown_generator.py 的 _process_chapter_pages 方法（章节Markdown模式）
  - [x] 确保章节生成模式也应用相同的内部插入逻辑（通过调用 _process_page_elements 自动实现）
  - [x] 验证 _process_page_elements 的修改已覆盖章节模式

- [x] 任务5: 测试验证
  - [x] 验证代码语法正确性（docx_generator.py 和 markdown_generator.py）

## 任务依赖

- [任务1] 是其他所有任务的前置任务
- [任务2] 和 [任务3] 可以并行执行
- [任务4] 依赖于 [任务3] 的完成
- [任务5] 在所有实现任务完成后执行
