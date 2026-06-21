# Checklist

- [x] `_parse_html_table` 接受 `table_bbox` 参数并计算每个单元格的 bbox 坐标
- [x] `_parse_json_response` 创建 PdfTable 时包含非空的 `row_heights` 和 `col_widths`
- [x] `_parse_json_response` 创建的每个 PdfCell 有非零 bbox（当 table bbox 有效时）
- [x] `_parse_ref_tags_response` 能从响应中检测并提取 HTML 表格
- [x] `_parse_markdown_response` 能从响应中检测并提取 HTML 表格
- [x] 现有 LLM OCR 测试 (`test_llm_ocr.py`) 仍然通过 (80 passed, 含 2 个新增测试)
- [x] 表格相关测试 (`test_markdown_table.py`, `test_table_grid.py`) 通过 (7 passed)
