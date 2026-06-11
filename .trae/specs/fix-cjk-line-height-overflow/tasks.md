# Tasks

- [x] Task 1: 计算原文行高倍率并在 `insert_textbox()` 中使用
  - [x] SubTask 1.1: 在 `_draw_translated_text` 方法中，根据 `bbox高度 / (字体大小 * 估算行数)` 计算原文行高倍率，设置下限为 1.0，默认值为 1.2
  - [x] SubTask 1.2: 在主渲染循环的 `insert_textbox()` 调用（第283行）中添加 `lineheight` 参数
  - [x] SubTask 1.3: 在缩小字体回退的 `insert_textbox()` 调用（第312行）中添加 `lineheight` 参数
  - [x] SubTask 1.4: 在截断文本回退的 `insert_textbox()` 调用（第342行）中添加 `lineheight` 参数
  - [x] SubTask 1.5: 在表格渲染中的 `insert_textbox()` 调用（第622行、第639行）中添加 `lineheight` 参数
  - [x] SubTask 1.6: 添加行高倍率计算的日志记录

- [x] Task 2: 验证修复效果
  - [x] SubTask 2.1: 运行现有测试确保无回归

# Task Dependencies

- Task 2 依赖 Task 1 完成
