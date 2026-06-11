# Tasks

- [ ] Task 1: 检测翻译文本中的换行符并扩展文本框高度
  - [ ] SubTask 1.1: 在 `_draw_translated_text` 方法中，在文本渲染前检测是否包含换行符（`\n`）
  - [ ] SubTask 1.2: 如果包含换行符，计算需要的行数：`len(translated_text.split('\n'))`
  - [ ] SubTask 1.3: 计算所需高度：`行数 * 字体大小 * 行高倍率`
  - [ ] SubTask 1.4: 如果所需高度 > 文本框高度，扩展文本框高度（上限为页面底部）
  - [ ] SubTask 1.5: 记录换行符处理的详细日志（行数、原始高度、扩展后高度）

- [ ] Task 2: 验证修复效果
  - [ ] SubTask 2.1: 运行翻译流程，检查包含换行符的标题是否正确显示
  - [ ] SubTask 2.2: 检查日志中是否有换行符处理的记录
  - [ ] SubTask 2.3: 检查是否避免了过度截断（截断比例应大于30%）

# Task Dependencies

- Task 2 依赖 Task 1 完成