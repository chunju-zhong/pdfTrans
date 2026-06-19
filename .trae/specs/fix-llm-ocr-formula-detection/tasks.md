# Tasks

- [x] Task 1: 在 `llm_extractor.py` 中添加公式检测方法 `_detect_formula`
  - [x] SubTask 1.1: 实现检测逻辑：判断文本是否整体被 `$...$`、`$$...$$`、`\(...\)`、`\[...\]` 包裹
  - [x] SubTask 1.2: 实现定界符清理逻辑：去除包裹符号，返回纯 LaTeX
  - [x] SubTask 1.3: 混合文本（公式+说明文字）不标记为公式

- [x] Task 2: 在 `_parse_ref_tags_response` 中集成公式检测
  - [x] SubTask 2.1: 创建 TextBlock 后调用 `_detect_formula`
  - [x] SubTask 2.2: 如果是公式，设置 `tb.is_formula = True`，用清理后的 LaTeX 替换 `block_text`

- [x] Task 3: 在 `_parse_json_response` 中集成公式检测
  - [x] SubTask 3.1: JSON 格式响应的文本块同样调用 `_detect_formula`

- [x] Task 4: 更新测试用例
  - [x] SubTask 4.1: 添加纯公式检测测试（`$...$`、`$$...$$`、`\(...\)`、`\[...\]`）
  - [x] SubTask 4.2: 添加混合文本不标记测试
  - [x] SubTask 4.3: 添加定界符清理测试
  - [x] SubTask 4.4: 添加 `_parse_ref_tags_response` 中公式标记集成测试

# Task Dependencies
- Task 2, Task 3 依赖 Task 1
- Task 4 依赖 Task 2, Task 3
