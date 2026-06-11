# Tasks

- [x] Task 1: 修改 `_add_table()` 方法，根据 `PdfTable.col_widths` 按比例设置 Word 表格列宽
  - [x] SubTask 1.1: 添加列宽比例计算逻辑（col_widths 可用时按比例映射到 6.5 英寸）
  - [x] SubTask 1.2: 添加 fallback 逻辑（col_widths 为空时从单元格 width 取最大值）
  - [x] SubTask 1.3: 使用 python-docx 的 `column.width` 和 `tblGrid` 设置列宽

- [x] Task 2: 修改 `_add_table()` 方法，根据 `PdfTable.row_heights` 设置 Word 表格行高
  - [x] SubTask 2.1: 添加行高设置逻辑（PDF 点转 Emu：1 点 = 12700 Emu）
  - [x] SubTask 2.2: 添加 fallback 逻辑（row_heights 为空时从单元格 height 取最大值）

- [x] Task 3: 修改 `_add_table()` 方法，根据 `PdfTable.bbox` 设置表格整体宽度
  - [x] SubTask 3.1: 计算 bbox 宽度并转换为英寸（1 点 = 1/72 英寸）
  - [x] SubTask 3.2: 限制最大宽度为 6.5 英寸
  - [x] SubTask 3.3: 设置表格 `autofit = False` 以固定宽度

# Task Dependencies

- Task 2 和 Task 3 依赖 Task 1（列宽设置是行高和整体宽度设置的基础）
