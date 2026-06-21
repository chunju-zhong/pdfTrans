# Tasks

- [x] Task 1: 修改 `table_bbox_map` 使用表格索引作为 key
  - [x] `_parse_ref_tags_response` 中用表格计数器作为 key（如 `table_bbox_map[len(table_bbox_map)] = pdf_bbox`）
  - [x] `_extract_tables_from_text` 中用 `enumerate` 获取索引，从 `table_bbox_map.get(table_index)` 查找 bbox

- [x] Task 2: 消除 `_parse_html_table` 重复解构
  - [x] 将 `table_bbox` 解构和 `table_width`/`table_height`/`rh`/`cw` 计算提到单元格循环前
  - [x] 循环内直接使用已计算的 `rh`/`cw` 变量

- [x] Task 3: 消除 `_extract_tables_from_text` 重复 bbox 检查
  - [x] 第 705 行检查后设为 None，第 710 行简化为 `if not table_bbox:`

- [x] Task 4: 提取 `'<table'` 为模块级常量 `TABLE_HTML_MARKER`
  - [x] 在文件顶部定义 `TABLE_HTML_MARKER = '<table'`
  - [x] 替换所有 3 处硬编码 `'<table'`

# Task Dependencies
- 无依赖，所有任务可并行执行
