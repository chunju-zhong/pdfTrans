# 合并单元格代码审查优化 Spec

## Why
代码审查发现合并单元格相关修改存在 3 个 MEDIUM 级别和 3 个 LOW 级别问题，包括遮挡逻辑过于激进、重复代码、调试日志级别不当等，需要优化以提升代码质量和可维护性。

## What Changes
- 简化 `compute_span_from_none_positions` 第三步验证逻辑，移除与 `covered_by_col_span` 的冲突检查
- 精确化 `pdf_generator.py` 中遮挡边界排除逻辑，只排除 col_span 的上/下边框和 row_span 的左/右边框
- 提取 `translation_service.py` 中重复的 `getattr(cell, 'row_span', 1)` 为辅助函数
- 将调试日志从 `logger.info` 降级为 `logger.debug`

## Impact
- Affected specs: optimize-merged-cell-rendering
- Affected code: modules/extractors/coordinate_utils.py, modules/pdf_generator.py, services/translation_service.py, modules/extractors/table_processor.py

## MODIFIED Requirements

### Requirement: compute_span_from_none_positions 第三步验证
第三步重新验证 col_span 和 row_span 时，不再检查 `(r, c) in covered_by_col_span`，因为第二步已经确保了 row_span 的正确性。第三步只需验证 bbox_matrix 中的 None 分布与计算出的 span 一致。

### Requirement: 遮挡边界排除逻辑
遮挡逻辑只排除以下边界位置：
- **col_span 合并单元格的上/下边框**：col_span 单元格跨多列，其上/下边框应完整绘制
- **row_span 合并单元格的左/右边框**：row_span 单元格跨多行，其左/右边框应完整绘制

不排除：
- row_span 合并单元格的上/下边框（这是合并单元格内部，横线应被遮挡）
- col_span 合并单元格的左/右边框（这是合并单元格内部，竖线应被遮挡）

### Requirement: translation_service 重复代码
提取辅助函数 `_get_cell_span(cell)` 返回 `(row_span, col_span)`，替代 9 处重复的 `getattr(cell, 'row_span', 1)` 调用。

### Requirement: 调试日志级别
将以下调试日志从 `logger.info` 降级为 `logger.debug`：
- `[网格线遮挡]` 相关日志
- `[表格HTML解析]` 相关日志
- `bbox_matrix 行` 相关日志
- `检测到合并单元格` 相关日志
