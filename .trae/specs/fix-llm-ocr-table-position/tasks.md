# Tasks

- [x] Task 1: 修改 `_parse_ref_tags_response` 保留表格的 `<|det|>` 坐标
  - [x] 在检测到 HTML 表格时，不再直接跳过，而是提取 `<|det|>` 坐标
  - [x] 将 det 坐标（归一化 0-999）转换为 PDF 点坐标
  - [x] 将坐标传递给 `_extract_tables_from_text` 或直接创建 PdfTable

- [x] Task 2: 修改 `_extract_tables_from_text` 接受 `table_bbox_map` 参数
  - [x] 新增 `table_bbox_map=None` 参数（dict: HTML片段 → bbox tuple）
  - [x] 当 map 中有匹配的 bbox 时优先使用，否则回退到估算
  - [x] 多表格时，无精确 bbox 的表格基于前一个表格高度向下偏移

- [x] Task 3: 更新 `_parse_ref_tags_response` 和 Markdown 分支的调用
  - [x] `_parse_ref_tags_response` 中构建 table_bbox_map 传入 `_extract_tables_from_text`
  - [x] Markdown 分支无需改动（无坐标信息）

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1, Task 2]
