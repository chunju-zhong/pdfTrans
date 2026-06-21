# Tasks

- [x] Task 1: 修复 `_parse_response` 格式检测优先级，`<|ref|>` 标签优先于 JSON
  - [x] SubTask 1.1: 在 `_parse_response` 中，先检查 `<|ref|>` 标签，再尝试 JSON 提取
  - [x] SubTask 1.2: 验证当前工作区代码已实现此优先级（确认现有修改正确）

- [x] Task 2: 移除 `_extract_json` 的第3级容错（花括号查找）
  - [x] SubTask 2.1: 删除 `_extract_json` 中 `text.find('{')` + `text.rfind('}')` + `json.loads(text[start:end+1])` 的逻辑
  - [x] SubTask 2.2: 保留第1级（直接解析）和第2级（```json``` 代码块）容错

- [x] Task 3: 增加 `_parse_json_response` 的格式解析日志
  - [x] SubTask 3.1: 在 `_parse_json_response` 入口处添加 `"第{page_num}页LLM OCR使用JSON格式解析"` 日志

- [x] Task 4: 实现空解析结果回退机制
  - [x] SubTask 4.1: 在 `_parse_response` 中，当 JSON 解析返回空文本块时，继续尝试 `<|ref|>` 标签格式和 Markdown 格式
  - [x] SubTask 4.2: 当 `<|ref|>` 标签解析也返回空结果时，继续尝试 Markdown 格式

- [x] Task 5: 验证修复效果
  - [x] SubTask 5.1: 编写单元测试验证 `<|ref|>` 标签优先于 JSON 的场景
  - [x] SubTask 5.2: 编写单元测试验证空解析结果回退机制
  - [x] SubTask 5.3: 运行现有测试确保无回归

# Task Dependencies
- Task 2-4 依赖 Task 1（优先级修复后再处理其他改进）
- Task 5 依赖 Task 1-4 全部完成
