# Tasks

- [x] Task 1: 修改 `split_translated_result()` 按原始文本长度比例分配翻译文本
  - [x] SubTask 1.1: 在函数中计算各原始块的文本长度比例
  - [x] SubTask 1.2: 将均等分配 `target_len = ceil(remaining_len / remaining_blocks)` 改为按比例分配
  - [x] SubTask 1.3: 添加保护：非最后一个块的 `actual_end` 不超过 `translation_len - min_characters_per_block * remaining_blocks`
  - [x] SubTask 1.4: 确保空块处理逻辑仍有效
  - [x] SubTask 1.5: 添加按比例分配的日志记录

- [x] Task 2: 验证修复效果
  - [x] SubTask 2.1: 运行现有测试确保无回归

# Task Dependencies

- Task 2 依赖 Task 1 完成
