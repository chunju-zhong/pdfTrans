# Tasks

- [x] Task 1: 修改 split_translated_result 函数添加换行符检测逻辑
  - [x] SubTask 1.1: 在函数开头检测翻译结果中的换行符数量
  - [x] SubTask 1.2: 根据换行符数量与原始块数量的关系选择拆分策略
  - [x] SubTask 1.3: 添加日志记录换行符检测结果

- [x] Task 2: 实现以换行符拆分的辅助函数 _split_by_newlines
  - [x] SubTask 2.1: 以换行符为分隔点拆分翻译文本
  - [x] SubTask 2.2: 处理行数与原始块数不匹配的情况
  - [x] SubTask 2.3: 分配拆分结果到原始块

- [x] Task 3: 实现混合拆分的辅助函数 _split_by_newlines_and_ratio
  - [x] SubTask 3.1: 先以换行符拆分前部分文本
  - [x] SubTask 3.2: 剩余原始块分配空文本
  - [x] SubTask 3.3: 添加日志记录混合拆分过程

- [x] Task 4: 实现处理多余换行符的辅助函数 _split_with_excess_newlines
  - [x] SubTask 4.1: 计算需要替换的换行符数量
  - [x] SubTask 4.2: 保留前 N-1 个换行符，替换多余的为空格
  - [x] SubTask 4.3: 合并多余行到最后一行

- [x] Task 5: 添加单元测试验证换行符拆分逻辑
  - [x] SubTask 5.1: 测试换行符数量匹配的拆分
  - [x] SubTask 5.2: 测试换行符少于原始块的拆分
  - [x] SubTask 5.3: 测试换行符多于原始块的拆分
  - [x] SubTask 5.4: 测试无换行符的拆分（原有逻辑）

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 1, Task 2, Task 3, Task 4]