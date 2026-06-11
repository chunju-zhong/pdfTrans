# Tasks

- [x] Task 1: 将 `header` 从 `NON_BODY_LABELS` 移除
  - [x] SubTask 1.1: 在 `paddle_extractor.py` 中将 `NON_BODY_LABELS` 从 `{'footer', 'page_number', 'footnote', 'header'}` 改为 `{'footer', 'page_number', 'footnote'}`
  - [x] SubTask 1.2: 验证 `header` 标签的文本块现在默认 `is_body_text=True`

- [x] Task 2: 修复 `_add_similar_blocks` 短文本误判（实施 `fix-text-analyzer-false-positive-header-footer` spec）
  - [x] SubTask 2.1: 修改 `_add_similar_blocks` 函数，当两个文本块长度均<20字符时，仅当文本完全相同（相似度=100%）才标记为非正文
  - [x] SubTask 2.2: 当一个文本块长度<20字符而另一个≥20字符时，使用相似度≥95%的阈值
  - [x] SubTask 2.3: 当两个文本块长度均≥20字符时，保持当前相似度≥90%的阈值

- [x] Task 3: 增强 OCR 提取诊断日志
  - [x] SubTask 3.1: 在 `_process_page_layout` 的文本块创建处，确保 `[FONT_DEBUG]` 日志包含 `label` 和 `is_body_text` 信息

- [x] Task 4: 修复 `rec_texts` 长度不匹配时的级联失败
  - [x] SubTask 4.1: 当 `rec_texts` 长度与 `rec_boxes` 不匹配时，记录 WARNING 日志并保留 `textline_boxes`（不丢弃坐标数据）
  - [x] SubTask 4.2: 在 TEXT_LABELS 分支中，当 `_build_text_from_textlines` 返回 None 且 `content` 有值时，使用 `content` 创建 TextBlock（当前逻辑已正确，但需确认 `content` 不为空的情况被正确处理）
  - [x] SubTask 4.3: 当 `_build_text_from_textlines` 返回 None 且 `content` 也为空时，记录 WARNING 日志说明该块文本提取失败

- [x] Task 5: 修复补充捕获的"已处理"标记逻辑
  - [x] SubTask 5.1: 将 `processed_bboxes` 的收集从"遍历所有 parsing_res_list 块"改为"只收集成功创建 TextBlock 的块"（使用 `processed_pixel_bboxes`）
  - [x] SubTask 5.2: 补充捕获的前提条件从 `len(textline_texts) > 0` 放宽为 `len(textline_boxes) > 0`，当 `textline_texts` 为空时仍执行补充捕获

# Task Dependencies

- [Task 4] 和 [Task 5] 可并行
- [Task 5] 依赖 [Task 4] 的日志增强（SubTask 4.3）
