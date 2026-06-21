# Tasks

- [x] Task 1: 修复 `_parse_det_bbox` 支持多 bbox 解析
  - [x] SubTask 1.1: 修改 `_parse_det_bbox` 方法，解析 `<|det|>` 中所有 `[x1, y1, x2, y2]` 坐标组，返回 `list[tuple]` 而非单个 `tuple`
  - [x] SubTask 1.2: 使用 `json.loads` 或正则 `r'\[([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\]'` 解析每组坐标
  - [x] SubTask 1.3: 为多 bbox 解析编写单元测试，覆盖：双 bbox、单 bbox、空/格式错误
- [x] Task 2: 拆分多 bbox `<|ref|>` 块为多个 TextBlock
  - [x] SubTask 2.1: 修改 `_parse_ref_tags_response`，当 `_parse_det_bbox` 返回多个 bbox 时，按 `\n\n` 拆分 `actual_text` 为多个段落
  - [x] SubTask 2.2: 每个段落创建独立的 TextBlock，使用对应的 bbox（第 i 个段落使用第 i 个 bbox）
  - [x] SubTask 2.3: bbox 数量与段落数量不匹配时回退：只用第一个 bbox 创建单个 TextBlock
  - [x] SubTask 2.4: 单 bbox 时保持现有行为不拆分
  - [x] SubTask 2.5: 为多 bbox 拆分逻辑编写单元测试
- [x] Task 3: 新增跨行断词预处理函数
  - [x] SubTask 3.1: 在 `utils/text_processing.py` 中新增 `fix_line_break_hyphens(text)` 函数，使用正则 `(\w)- (\w)` 匹配跨行断词并合并
  - [x] SubTask 3.2: 确保不误修复合法连字符（如 `next-token`）
  - [x] SubTask 3.3: 在 `_parse_ref_tags_response`、`_parse_markdown_response`、`_parse_json_response` 中调用断词修复
  - [x] SubTask 3.4: 为断词修复编写单元测试

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] is independent of [Task 1] and [Task 2]
