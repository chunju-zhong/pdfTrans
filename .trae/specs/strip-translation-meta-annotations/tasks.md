# Tasks

- [ ] Task 1: 在 `_postprocess_text` 中添加元注释清除逻辑
  - [ ] SubTask 1.1: 添加正则匹配清除括号内的元注释：匹配 `（注：...）`、`（说明：...）`、`（备注：...）` 等模式，移除整个括号及内容
  - [ ] SubTask 1.2: 添加正则匹配清除末尾独立元注释：匹配 `注：...`、`说明：...` 等出现在文本末尾的独立说明
  - [ ] SubTask 1.3: 添加正则匹配清除翻译决策解释：匹配 `"XXX"译为"YYY"` 或 `「XXX」译为「YYY」` 等模式
  - [ ] SubTask 1.4: 清除后清理多余空格，确保不影响正常括号内容

- [ ] Task 2: 运行测试验证
  - [ ] SubTask 2.1: 运行 `pytest tests/ -x -q` 确保所有测试通过

# Task Dependencies

- Task 2 依赖于 Task 1 完成
