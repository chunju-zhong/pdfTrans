# Tasks

- [x] Task 1: 修改 `llm_extractor.py` 的 `_parse_html_table`，复用 `_expand_html_table` 生成矩形矩阵并裁剪 rowspan/colspan
  - [x] SubTask 1.1: 在 `_parse_html_table` 中引入 `_expand_html_table` 逻辑（参考 paddle_extractor.py:1478-1542），生成规整矩形矩阵替代锯齿数组
  - [x] SubTask 1.2: 在展开矩阵时裁剪 rowspan/colspan：`rowspan = min(rowspan, n_rows - row_idx)`，`colspan = min(colspan, n_cols - col_idx)`
  - [x] SubTask 1.3: 确保单元格 bbox 计算在矩形矩阵生成后进行（基于 row_idx/col_idx 和裁剪后的 rowspan/colspan）
  - [x] SubTask 1.4: 运行已有测试 `tests/test_llm_ocr.py` 中 `_parse_html_table` 相关用例，确认不回归

- [x] Task 2: 修改 `docx_generator.py` 的 `_add_table`，添加防御性边界检查
  - [x] SubTask 2.1: 修正 `num_cols` 计算：使用所有行中 `col_idx + col_span` 的最大值，而非 `len(table_data[0])`
  - [x] SubTask 2.2: 在 merge 操作前裁剪范围：`merge_row = min(i + row_span - 1, num_rows - 1)`，`merge_col = min(j + col_span - 1, num_cols - 1)`，仅在 merge 范围有效时执行 merge
  - [x] SubTask 2.3: 在写入单元格文本时，跳过 `j >= num_cols` 的单元格，避免 `word_table.cell(i, j)` 越界
  - [x] SubTask 2.4: 在设置列宽 `word_table.columns[col_idx]` 时添加 `col_idx < len(word_table.columns)` 检查

# Task Dependencies
- Task 2 独立于 Task 1，可并行实施
- Task 1 是源头修复（让数据结构正确），Task 2 是防御性修复（让消费者更健壮），两者互补
