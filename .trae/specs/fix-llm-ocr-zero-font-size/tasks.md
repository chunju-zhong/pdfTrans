# Tasks

- [x] Task 1: 修改 `pdf_generator.py`，当 `original_font_size == 0` 时根据 bbox 估算字体大小
  - [ ] 在 `original_font_size = full_block.font_size` 之后，添加字体大小为0的估算逻辑
  - [ ] `font_size = 0` 且 `bbox_height > 0`：估算 `font_size = bbox_height * 0.75`，上限 36pt
  - [ ] `font_size = 0` 且 `bbox_height == 0`：默认 12pt
  - [ ] 添加日志记录估算过程

# Task Dependencies
- 无
