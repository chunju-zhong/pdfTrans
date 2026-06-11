# Tasks

- [x] Task 1: 修复 compute_span_from_none_positions 向下扫描逻辑
  - [x] 向下扫描时验证整行段（col_idx 到 col_idx+col_span-1）均为 None
  - [x] 只有整行段全为 None 时才增加 row_span

- [x] Task 2: 验证
  - [x] 编译检查
  - [x] 运行相关测试

# Task Dependencies

- Task 2 depends on Task 1
