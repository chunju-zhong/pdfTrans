# Tasks

- [x] Task 1: 文本框背景 padding 使用合理计算公式
  - [x] SubTask 1.1: 将 `bg_padding` 从 `original_font_size` 改为 `max(3, min(original_font_size * 0.4, 8))`
  - [x] SubTask 1.2: 将 `bg_rect` 的 X 方向改为 `max(rect.x0 - bg_padding, 0)` 和 `min(rect.x1 + bg_padding, page.rect.width)`
  - [x] SubTask 1.3: 验证语法正确（python 编译检查通过，现有测试通过）

- [x] Task 2: 表格单元格背景增加水平 padding
  - [x] SubTask 2.1: 在 `pdf_generator.py` 的表格单元格背景绘制中，为白色背景矩形水平方向添加 `2pt` padding（使用 `cell_bg_rect` 分离背景和边框）
  - [x] SubTask 2.2: 验证语法正确（python 编译检查通过）

- [x] Task 3: PP-StructureV3 漏检文本的通用捕获机制
  - [x] SubTask 3.1: 在 `paddle_extractor.py` 的 `_process_page_layout` 方法末尾，收集所有已处理 LayoutBlock 的 bbox 集合
  - [x] SubTask 3.2: 实现 textline 覆盖检测逻辑：遍历 `overall_ocr_res` 的 textline，检查是否被任何已处理 bbox 覆盖
  - [x] SubTask 3.3: 未被覆盖的 textline 按垂直邻近关系聚合成文本块，创建 `TextBlock` 加入 `text_blocks` 列表
  - [x] SubTask 3.4: 在 `figure_caption` 标签分支中，使用 `_build_text_from_textlines` 提取文本并创建 `TextBlock`
  - [x] SubTask 3.5: 添加诊断日志（被覆盖/未被覆盖的 textline 数量、创建的补充 TextBlock 数量）

- [ ] Task 4: 运行程序验证修复效果（需要用户提供包含表格的测试 PDF）
  - [ ] SubTask 4.1: 对包含表格和图片的 PDF 运行程序
  - [ ] SubTask 4.2: 检查日志中 `[SUPPLEMENT]` 和背景 padding 的日志
  - [ ] SubTask 4.3: 检查 PDF 输出视觉效果

# Task Dependencies

- Task 3 依赖 Task 1, Task 2（漏检文本需要正确的背景覆盖来展示）
- Task 4 依赖 Task 1, Task 2, Task 3（需要用户提供测试 PDF 运行端到端验证）
