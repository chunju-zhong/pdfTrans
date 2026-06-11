# Tasks

- [x] Task 1: 修复 compute_span_from_none_positions 向右扫描逻辑
  - [x] 先确定 col_span=1 时的 row_span（向下扫描单列）
  - [x] 基于 row_span 向右扫描确定 col_span（验证整列段均为 None）
  - [x] 基于 col_span 重新验证 row_span（验证最底行整行段均为 None，否则缩减 row_span）

- [x] Task 2: 修复遮挡逻辑——排除合并单元格边界位置
  - [x] 收集所有合并单元格的边界位置（上/下/左/右边框）
  - [x] 从遮挡信息中排除边界位置（画线优先于不画线）
  - [x] 添加 bbox_matrix None 分布日志

- [x] Task 3: 验证
  - [x] 编译检查
  - [x] 运行相关测试

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 1 and Task 2
