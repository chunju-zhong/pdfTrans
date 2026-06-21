# 修复 LLM OCR 代码审查问题 Spec

## Why
代码审查发现 `table_bbox_map` 使用 HTML 全文作为 dict key 导致匹配极易失败（HIGH），以及多处冗余代码和重复字符串（MEDIUM/LOW）。

## What Changes
- `table_bbox_map` 改用表格索引（第几个 `<table>`）作为 key，避免 HTML 文本空白差异导致匹配失败
- `_parse_html_table` 消除 `table_bbox` 重复解构
- `_extract_tables_from_text` 消除 bbox 有效性重复检查
- 提取 `'<table'` 为模块级常量

## Impact
- Affected code: [llm_extractor.py](modules/ocr/llm_extractor.py) `_parse_ref_tags_response`、`_extract_tables_from_text`、`_parse_html_table`
- Affected specs: fix-llm-ocr-table-position

## ADDED Requirements

### Requirement: table_bbox_map 使用索引作为 key
`_parse_ref_tags_response` 和 `_extract_tables_from_text` 中的 `table_bbox_map` SHALL 使用表格索引（整数）作为 key，而非 HTML 全文字符串。

#### Scenario: ref 标签包含表格
- **WHEN** `<|ref|>` 块包含第 N 个 `<table>` 标签且有有效 det 坐标
- **THEN** `table_bbox_map[N] = pdf_bbox`

#### Scenario: _extract_tables_from_text 查找 bbox
- **WHEN** 处理第 N 个 `<table>` 匹配
- **THEN** 从 `table_bbox_map.get(N)` 获取 bbox

### Requirement: 消除 _parse_html_table 重复解构
`_parse_html_table` 中 `table_bbox` 的解构和 `table_width`/`table_height` 计算 SHALL 只在循环前执行一次。

### Requirement: 消除 _extract_tables_from_text 重复 bbox 检查
`_extract_tables_from_text` 中 bbox 有效性检查 SHALL 只执行一次，设为 None 后直接进入估算分支。

### Requirement: 提取重复字符串为常量
`'<table'` 字符串 SHALL 提取为模块级常量 `TABLE_HTML_MARKER`。
