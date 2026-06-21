# Tasks

- [x] Task 1: 在PdfCell模型中新增`estimated_lines`字段
  - [x] SubTask 1.1: 在`__init__`中新增`estimated_lines`参数，默认值0
  - [x] SubTask 1.2: 在`from_dict`中读取`estimated_lines`字段，默认0
  - [x] SubTask 1.3: 在`to_dict`中输出`estimated_lines`字段
- [x] Task 2: 重构`_parse_html_table`为"先行高后列宽"迭代优化
  - [x] SubTask 2.1: 实现Step 1 - 用等宽列初始估算每行行数和行高
  - [x] SubTask 2.2: 实现Step 2 - 钳位行高到原始bbox（超出按比例缩小，不足按比例放大）
  - [x] SubTask 2.3: 实现Step 3 - 根据钳位后行高反推列宽：每单元格所需最小列宽 = display_width / available_lines，每列权重取最大值，按比例分配总宽度，钳位10%-50%
  - [x] SubTask 2.4: 实现Step 4-6迭代循环：用新列宽重算行高→钳位→反推列宽，直到行高变化<0.5pt或达到3次迭代
  - [x] SubTask 2.5: 在迭代完成后将每个单元格的最终估算行数写入`cell.estimated_lines`
  - [x] SubTask 2.6: 确保空单元格的`estimated_lines`为0
- [x] Task 3: 在`_draw_translated_table`中利用`estimated_lines`优化渲染
  - [x] SubTask 3.1: 绘制单元格前，根据`estimated_lines`和单元格高度计算可容纳的最大字体大小
  - [x] SubTask 3.2: 如果预判文本可能溢出，直接使用较小的初始字体而非从原始字体开始逐步缩小
  - [x] SubTask 3.3: `estimated_lines`为0时回退到现有逻辑（兼容旧数据）

# Task Dependencies
- Task 2 依赖 Task 1（需要PdfCell先有estimated_lines字段）
- Task 3 依赖 Task 1 + Task 2（需要识别阶段先写入estimated_lines）
