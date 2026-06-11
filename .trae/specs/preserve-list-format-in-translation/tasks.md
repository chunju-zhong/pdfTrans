# Tasks

- [x] Task 1: 修改 `_preprocess_text` 保留列表换行
  - [x] SubTask 1.1: 将 `' '.join(text.split())` 替换为按 `\n` 分割、每行内压缩空白、过滤空行、再用 `\n` 重新连接

- [x] Task 2: 修改 `_postprocess_text` 保留列表换行
  - [x] SubTask 2.1: 将 `' '.join(processed_text.split())` 替换为按 `\n` 分割、每行内压缩空白、过滤空行、再用 `\n` 重新连接

- [x] Task 3: 在翻译 prompt 中增加列表格式保持规则
  - [x] SubTask 3.1: 新增规则 14：保持原文列表格式，保留换行和项目符号（如 •、-、数字编号等），不将列表项合并为连续段落

- [x] Task 4: 运行测试验证
  - [x] SubTask 4.1: 运行 `pytest tests/ -x -q` 确保所有测试通过（362 passed, 1 skipped）

# Task Dependencies

- Task 1、Task 2、Task 3 无依赖，可并行
- Task 4 依赖于 Task 1、Task 2、Task 3 完成
