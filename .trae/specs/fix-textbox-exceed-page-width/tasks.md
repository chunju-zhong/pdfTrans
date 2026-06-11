# Tasks

- [x] Task 1: 修复 pdf_generator.py 溢出重试时文本框扩展逻辑
  - [x] SubTask 1.1: 修改第 302-314 行，扩展文本框时限制右边界不超过页面宽度 `min(current_rect.x0 + new_width, page.rect.width)`
  - [x] SubTask 1.2: 限制下边界不超过页面高度 `min(current_rect.y0 + new_height, page.rect.height)`
  - [x] SubTask 1.3: 添加日志记录扩展后的文本框是否触及页面边界

- [x] Task 2: 修复 paddle_extractor.py tight bbox 容差和页面宽度限制
  - [x] SubTask 2.1: 将 `_compute_tight_bbox()` 第 472 行的容差从 1.3 降低到 1.1
  - [x] SubTask 2.2: 在 tight bbox 计算后增加页面宽度限制，确保不超出页面
  - [x] SubTask 2.3: 添加日志记录 tight bbox 与布局 bbox 的宽度比较

- [x] Task 3: 验证修复效果
  - [x] SubTask 3.1: 运行现有测试确保无回归
  - [x] SubTask 3.2: 检查 test_pdf_generator.py 中 test_text_overflow_handling 测试通过

# Task Dependencies
- [Task 1] 和 [Task 2] 独立，可并行执行
- [Task 3] 依赖 [Task 1] 和 [Task 2]
