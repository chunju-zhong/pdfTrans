# Tasks
- [x] Task 1: 将文本块 redaction 背景从白色改为透明
  - [x] 修改第497行 `page.add_redact_annot(bg_rect, fill=(1, 1, 1))` 为 `page.add_redact_annot(bg_rect, fill=None)`
- [x] Task 2: 将表格单元格 redaction 背景从白色改为透明
  - [x] 修改第1064行 `page.add_redact_annot(cell_bg_rect, fill=(1, 1, 1))` 为 `page.add_redact_annot(cell_bg_rect, fill=None)`
- [x] Task 3: 验证生成PDF中文本框背景为透明，无白色方块

# Task Dependencies
- Task 2 和 Task 1 无依赖关系，可并行执行
- Task 3 依赖 Task 1 和 Task 2
