# Tasks
- [x] Task 1: 将文本块 redaction 背景从透明恢复为白色
  - [x] 修改第516行 `page.add_redact_annot(bg_rect, fill=None)` 为 `page.add_redact_annot(bg_rect, fill=(1, 1, 1))`
- [x] Task 2: 将表格单元格 redaction 背景从透明恢复为白色
  - [x] 修改第1083行 `page.add_redact_annot(cell_bg_rect, fill=None)` 为 `page.add_redact_annot(cell_bg_rect, fill=(1, 1, 1))`

# Task Dependencies
- Task 1 和 Task 2 无依赖关系，可并行执行
