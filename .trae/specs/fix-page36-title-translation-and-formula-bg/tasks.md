# Tasks

- [x] Task 1: 修复 header 标签标题不翻译的问题
  - [x] SubTask 1.1: 在 `paddle_extractor.py` 中将 `header` 从 `NON_BODY_LABELS` 移除，使 header 标签的文本块默认 `is_body_text=True`，参与翻译

- [x] Task 2: 修复公式渲染时原文背景未覆盖的问题
  - [x] SubTask 1.1: 在 `pdf_generator.py` 的公式渲染分支中，在 `insert_image` 之前先绘制白色背景矩形覆盖原文区域

# Task Dependencies

- [Task 1] 独立
- [Task 2] 独立
