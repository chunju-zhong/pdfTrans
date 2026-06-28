# Tasks

- [x] Task 1: 修改 `_generate_system_prompt` 第 11 条，覆盖目录与多行结构化文本的换行保留
  - [x] SubTask 1.1: 在 [modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py) 的 `_generate_system_prompt` 方法中，修改第 11 条"列表格式保持"，明确覆盖**目录**（条目+页码的多行结构，含序号. 条目 页码、含前导点号的目录行）及其它多行结构化文本
  - [x] SubTask 1.2: 措辞语言无关，不限定具体语言；要求翻译时保留逐行换行，不合并为连续段落
  - [x] SubTask 1.3: 保持第 11 条在"三、保持格式"区块的位置，不改动其它条款（7-10、12）与其它区块

- [x] Task 2: 修改 `_FORMAT_SYSTEM_PROMPT`，在"严格规则"区块新增"结构保留"规则
  - [x] SubTask 2.1: 在 `_FORMAT_SYSTEM_PROMPT` 的"严格规则"区块新增一条结构保留规则：保留目录、列表、多行结构化文本的逐行换行；识别目录模式（条目+页码、序号. 条目 页码、含前导点号的目录行）并逐行保留；不得将结构化文本的换行替换为空格或合并多行为一行
  - [x] SubTask 2.2: 补充"保留原文的换行结构，不得擅自合并行或把换行改为空格"
  - [x] SubTask 2.3: 保持"输出格式要求"区块（---块N--- 标记相关）与其它严格规则不变（上一 spec 已修复的丢块问题保持不变）

- [x] Task 3: 验证修改不破坏现有测试
  - [x] SubTask 3.1: 运行 `tests/test_translator.py`，确认全部测试通过（提示词是字符串常量，现有测试 mock 了 LLM 响应，不依赖具体 prompt 文本，应不受影响）
  - [x] SubTask 3.2: 检查测试中是否有针对 `_generate_system_prompt` 第 11 条或 `_FORMAT_SYSTEM_PROMPT` 文本的断言；若有需同步更新

# Task Dependencies
- Task 3 依赖 Task 1、Task 2 完成
- Task 1 与 Task 2 都修改 translator.py（不同位置：第 11 条在 ~line 315，_FORMAT_SYSTEM_PROMPT 在 lines 8-36），由同一 sub-agent 顺序执行避免冲突
