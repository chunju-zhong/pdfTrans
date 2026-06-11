# Tasks

- [x] Task 1: 简化 compute_span_from_none_positions 第三步验证逻辑
  - [x] 移除第三步中 `(r, c) in covered_by_col_span` 检查，只保留 bbox_matrix None 分布验证
  - [x] 运行单元测试验证无回归

- [x] Task 2: 精确化 pdf_generator.py 遮挡边界排除逻辑
  - [x] 修改边界排除：只排除 col_span 单元格的上/下边框和 row_span 单元格的左/右边框
  - [x] 不排除 row_span 单元格的上/下边框（合并内部横线应被遮挡）
  - [x] 不排除 col_span 单元格的左/右边框（合并内部竖线应被遮挡）

- [x] Task 3: 提取 translation_service.py 重复的 getattr 代码
  - [x] 在 translation_service.py 中添加 `_get_cell_span(cell)` 辅助函数
  - [x] 替换所有 `getattr(cell, 'row_span', 1)` 和 `getattr(cell, 'col_span', 1)` 调用

- [x] Task 4: 降级调试日志级别
  - [x] pdf_generator.py 中 `[网格线遮挡]` 等日志从 info 改为 debug
  - [x] table_processor.py 中 `检测到合并单元格` 和 `bbox_matrix 行` 等日志从 info 改为 debug
  - [x] paddle_extractor.py 中 `[表格HTML解析]` 等日志从 info 改为 debug

# Task Dependencies
- Task 1, Task 2, Task 3, Task 4 相互独立，可并行执行
