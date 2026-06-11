# Tasks

- [x] Task 1: PdfCell 和 PdfTable 模型新增 alignment 属性
  - [x] SubTask 1.1: PdfCell 新增 alignment 参数（默认 0），更新 from_dict/to_dict
  - [x] SubTask 1.2: PdfTable 新增 alignment 参数（默认 1），更新 from_dict/to_dict

- [x] Task 2: 提取层提取单元格对齐方式
  - [x] SubTask 2.1: coordinate_utils.py 新增 `extract_cell_alignment()` 函数（利用字符 bbox 计算文本整体 bbox，与单元格 bbox 比较提取对齐）
  - [x] SubTask 2.2: table_processor.py 在 `extract_table_cells_by_bbox` 中利用已分配的字符 bbox 提取对齐，传入 cell_info
  - [x] SubTask 2.3: table_processor.py 在创建 PdfCell 时从 cell_info 获取 alignment
  - [x] SubTask 2.4: paddle_extractor.py 在 OCR 表格提取时利用 textline bbox 提取对齐

- [x] Task 3: 提取层提取表格整体对齐
  - [x] SubTask 3.1: coordinate_utils.py 新增 `extract_table_alignment()` 函数（比较 bbox 中心与页面中心）
  - [x] SubTask 3.2: table_processor.py 在创建 PdfTable 时设置 alignment

- [x] Task 4: PDF 生成器使用单元格对齐
  - [x] SubTask 4.1: pdf_generator.py 表格单元格绘制使用 `cell.alignment` 替代硬编码 `align=1`

- [x] Task 5: Word 生成器使用单元格和表格对齐
  - [x] SubTask 5.1: docx_generator.py 单元格段落对齐使用 `cell.alignment`
  - [x] SubTask 5.2: docx_generator.py 表格整体对齐使用 `table.alignment` 替代硬编码 CENTER

# Task Dependencies
- Task 2, 3 依赖 Task 1（模型先有 alignment 字段）
- Task 4, 5 依赖 Task 1, 2, 3（生成器依赖提取层提供的 alignment 数据）
