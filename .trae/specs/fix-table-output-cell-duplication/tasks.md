# Tasks

- [x] Task 1: 在 translator.py 的 system prompt 中增加分隔符保留规则
  - [x] SubTask 1.1: 在 `_generate_system_prompt` 规则列表末尾新增第17条：保留 "|||" 分隔符规则

- [x] Task 2: 在 translate_table_row 中增加分隔符数量不匹配的 fallback
  - [x] SubTask 1.1: 检测 `split(SEPARATOR)` 结果数量与原始单元格数量是否匹配
  - [x] SubTask 1.2: 不匹配时逐个单元格单独翻译作为 fallback
  - [x] SubTask 1.3: 记录警告日志

- [x] Task 3: 验证
  - [x] SubTask 3.1: 语法检查和单元测试（390 passed, 1 skipped）
  - [ ] SubTask 3.2: 运行程序验证第20页表格 Output 单元格翻译正确（需用户提供测试 PDF）

# Task Dependencies

- Task 2 依赖 Task 1（prompt 强化 + fallback 双保险）
- Task 3 依赖 Task 1, Task 2
