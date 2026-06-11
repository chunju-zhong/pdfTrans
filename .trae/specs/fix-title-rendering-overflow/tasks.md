# Tasks

- [x] Task 1: 修改 `_generate_system_prompt` 翻译提示词规则
  - [x] SubTask 1.1: 修改规则 2：将"增加必要的过渡"改为"自然过渡：保持原文逻辑关系，仅在必要时添加过渡词，不额外扩展内容"
  - [x] SubTask 1.2: 修改规则 4：将"书写习惯：句子和段落有长有短"改为"简洁精炼：翻译应简洁精炼，长度与原文相当，不添加解释性说明或扩展内容"
  - [x] SubTask 1.3: 新增规则 12：翻译长度应与原文相近，避免翻译膨胀。标题、列表项等短文本尤其应保持简洁，不做任何解释性扩展

- [x] Task 2: 运行测试验证
  - [x] SubTask 2.1: 运行 `pytest tests/ -x -q` 确保所有测试通过（362 passed, 1 skipped）

# Task Dependencies

- Task 2 依赖于 Task 1 完成
