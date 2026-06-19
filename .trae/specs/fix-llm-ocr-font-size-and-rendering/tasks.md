# Tasks

- [x] Task 1: 改进 LLM OCR 字体大小估算（面积法）
  - [x] 在 `_parse_ref_tags_response` 中，计算 bbox_width 和 text_length
  - [x] 实现 `font_size_by_area = sqrt(bbox_width * bbox_height / (text_length * 0.66))`
  - [x] 取 `min(font_size_by_lines, font_size_by_area, 36)` 作为最终估算
  - [x] 在 `_parse_json_response` 中应用相同的改进
  - [x] 添加日志记录面积法估算过程

- [x] Task 2: 增大水平方向 redaction padding
  - [x] 修改 `pdf_generator.py` 中 `_draw_translated_text` 方法的 redaction padding 计算
  - [x] 水平 padding: `max(5, min(font_size * 0.5, 12))`
  - [x] 垂直 padding: `max(3, min(font_size * 0.3, 6))`
  - [x] 分别计算水平和垂直 padding，应用到 bg_rect 的四个方向

- [x] Task 3: 重启服务器并验证
  - [x] 重启 python app.py 加载新代码
  - [x] 重新翻译第 5 页验证三个问题是否修复

# Task Dependencies
- Task 1 修改 `llm_extractor.py`，与 Task 2 无依赖，可并行
- Task 2 修改 `pdf_generator.py`
- Task 3 依赖 Task 1-2 全部完成
