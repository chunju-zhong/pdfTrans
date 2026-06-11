# Tasks

- [x] Task 1: merge_semantic_blocks 添加公式块隔离
  - [x] SubTask 1.1: 在合并循环开头添加公式块检查：如果当前块 `is_formula=True`，结束当前合并块，公式块单独成新块
  - [x] SubTask 1.2: 如果当前合并块第一个原始块是公式块，结束当前合并块，当前块开始新合并块
  - [x] SubTask 1.3: 第一个块为公式块时的初始化处理

- [x] Task 2: merge_semantic_blocks_with_llm 添加公式块隔离
  - [x] SubTask 2.1: 与 Task 1 相同逻辑，在 LLM 合并方法中添加公式块隔离
  - [x] SubTask 2.2: 第一个块为公式块时的初始化处理

- [x] Task 3: merge_semantic_blocks_with_llm_two_phase 添加公式块隔离
  - [x] SubTask 3.1: 与 Task 1 相同逻辑，在两阶段合并方法中添加公式块隔离
  - [x] SubTask 3.2: 第一个块为公式块时的初始化处理

- [x] Task 4: 验证
  - [x] SubTask 4.1: 语法检查通过
  - [x] SubTask 4.2: 确认公式块不会被合并到文本块中

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 1, 2, 3
