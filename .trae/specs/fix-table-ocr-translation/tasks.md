# Tasks

- [x] Task 1: 修复 OCR 模式章节关联（文本块+表格+图像）
  - [x] SubTask 1.1: 在 `pdf_extractor.py` 的 OCR 模式代码路径中，提取结果返回前添加章节关联流程：`chapter_identifier.reset()` → `extract_bookmarks()` → `associate_text_blocks()` → `associate_tables()` → `associate_images()`（对齐非 OCR 模式第345-402行的逻辑）
  - [x] SubTask 1.2: 处理分批 OCR 的情况：在 `_merge_batch_results` 返回后执行章节关联（而非每批执行）
  - [x] SubTask 1.3: 确保 OCR 模式下 `chapter_identifier` 已正确初始化

- [x] Task 2: 修复多表格 bbox 匹配 bug
  - [x] SubTask 2.1: 修改 `paddle_extractor.py` 的 `_process_page_tables` 方法，将 `parsing_res_list` 中所有 `table` block 的 bbox 收集为列表
  - [x] SubTask 2.2: 按 `table_res_list` 的索引匹配对应的 bbox（第 N 个 table_res 使用第 N 个 table block 的 bbox）

- [x] Task 3: OCR 模式补充单元格 bbox
  - [x] SubTask 3.1: 在 `_parse_html_table` 或 `_process_page_tables` 中，基于表格 bbox 和行列数计算每个单元格的等分 bbox
  - [x] SubTask 3.2: 将计算的 bbox 赋值给每个 PdfCell（替代 `(0,0,0,0)`）
  - [x] SubTask 3.3: 同时计算 `row_heights` 和 `col_widths` 并赋值给 PdfTable

- [x] Task 4: 修复 OCR 模式 PDF 表格渲染位置
  - [x] SubTask 4.1: 修改 `pdf_generator.py` 的 `_draw_translated_table` 方法，当 `row_heights` 和 `col_widths` 为空但 `table.bbox` 有效时，基于 bbox 等分计算单元格位置
  - [x] SubTask 4.2: 移除硬编码坐标回退逻辑（`x0=50+j*100, y0=200+i*30`）

- [x] Task 5: 表格翻译批量化
  - [x] SubTask 5.1: 修改 `translation_service.py` 的 `_process_table_translation` 方法，将每行单元格文本用分隔符拼接后一次翻译
  - [x] SubTask 5.2: 翻译结果按分隔符拆分回各单元格
  - [x] SubTask 5.3: 处理分隔符冲突（选择单元格文本中不出现的分隔符）
  - [x] SubTask 5.4: 更新进度计算逻辑（从按单元格改为按行）

- [x] Task 6: Word 表格添加基本样式
  - [x] SubTask 6.1: 修改 `docx_generator.py` 的 `_add_table` 方法，添加表格边框样式
  - [x] SubTask 6.2: 设置单元格字体和字号

- [x] Task 7: Markdown 表格智能表头检测
  - [x] SubTask 7.1: 修改 `markdown_generator.py` 的 `_convert_table_to_markdown` 方法，检测首行是否为表头
  - [x] SubTask 7.2: 首行非表头时添加空表头行

# Task Dependencies

- [Task 1] 独立
- [Task 2] 独立
- [Task 3] 依赖 [Task 2]（需要正确的表格 bbox 才能计算单元格 bbox）
- [Task 4] 依赖 [Task 3]（单元格 bbox 和 row_heights/col_widths 可用后 PDF 渲染更准确，但也需要单独处理等分回退）
- [Task 5] 独立
- [Task 6] 独立
- [Task 7] 独立
