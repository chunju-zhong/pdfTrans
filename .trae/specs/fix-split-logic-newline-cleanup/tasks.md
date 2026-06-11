# Tasks

- [ ] Task 1: 在拆分逻辑中添加标题识别和换行符清理
  - [ ] SubTask 1.1: 在 `text_processing.py` 中添加 `_is_title_block` 函数，判断原始块是否是标题
  - [ ] SubTask 1.2: 在 `split_translated_result` 函数中，拆分后判断是否是标题并清理换行符
  - [ ] SubTask 1.3: 清理策略：将 `\n` 替换为空格，清理多余空格
  - [ ] SubTask 1.4: 记录清理日志：原始文本、清理后文本、换行符数量

- [ ] Task 2: 验证修复效果
  - [ ] SubTask 2.1: 运行翻译流程，检查标题是否正确显示（不包含换行符）
  - [ ] SubTask 2.2: 检查日志中是否有拆分换行符清理的记录
  - [ ] SubTask 2.3: 检查标题是否未被截断或过度截断

# Task Dependencies

- Task 2 依赖 Task 1 完成