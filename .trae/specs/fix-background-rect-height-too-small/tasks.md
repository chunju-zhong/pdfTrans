# Tasks

- [x] Task 1: 修复白色背景高度偏小
  - [x] SubTask 1.1: 在 `pdf_generator.py` 绘制白色背景时，基于 `font_size * 0.3` 向上下扩展背景矩形
  - [x] SubTask 1.2: 背景矩形 clamp 到页面边界内（y0 >= 0, y1 <= page.rect.height）
  - [x] SubTask 1.3: 确保文本插入仍使用原始 `block_bbox`，不受背景扩展影响

- [x] Task 2: 修复语义合并时 max_height 取最大值而非累加
  - [x] SubTask 2.1: 在 `text_processing.py` 合并逻辑中，将 `max_height = max(...)` 改为 `curr_bbox[3] - first_bbox[1]`
  - [x] SubTask 2.2: 验证 `max_width` 逻辑不受影响（仍取最大值）

# Task Dependencies
- Task 1 和 Task 2 相互独立，已并行执行完成
