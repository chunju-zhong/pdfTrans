# Tasks

- [x] Task 1: 在 `_format_with_layout_model` 中实现占位符替换保护
  - [x] SubTask 1.1: 发送前，用 regex 提取 `$$...$$` 和 `$...$` 公式，替换为 `__FORMULA_N__` 占位符
  - [x] SubTask 1.2: 用含占位符的文本构建 LLM 用户提示词
  - [x] SubTask 1.3: LLM 返回后，将占位符恢复为原始公式内容

- [x] Task 2: 验证
  - [x] SubTask 2.1: 语法检查通过（`python -m py_compile` 退出码 0）
  - [x] SubTask 2.2: 2 个现有测试通过
  - [ ] SubTask 2.3: 端到端验证：翻译包含 `\mathsf`、`\mathrm`、`\frac` 等复杂公式的 PDF，检查 MD 输出中公式内容与原文完全一致

# Task Dependencies

无
