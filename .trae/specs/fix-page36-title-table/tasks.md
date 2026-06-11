# Tasks

- [ ] Task 1: 添加未知标签的 fallback 处理
  - [ ] SubTask 1.1: 在 `paddle_extractor.py` 的 `_process_page_layout` 方法中，为 `paragraph_title` 添加处理分支，归类为 title 类型文本块
  - [ ] SubTask 1.2: 为 `vision_footnote` 添加处理分支，归类为普通 text 文本块
  - [ ] SubTask 1.3: 为其他未知标签添加通用 fallback，归类为 text 并记录 WARNING

- [ ] Task 2: 启用表格识别
  - [ ] SubTask 2.1: 确认当 `OCR_SKIP_TABLE=False` 时 `use_table=True` 正确传入 PPStructureV3

# Task Dependencies

- [Task 1] 独立
- [Task 2] 独立
