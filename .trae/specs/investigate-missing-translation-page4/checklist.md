- [x] OCR 版面标签诊断日志已添加：`_process_page_layout` 记录所有 PaddleOCR 返回的标签及对应文本内容

- [x] 确认第四页 "Overflow surface load" 内容的 PaddleOCR 标签类型（已添加 [LABEL_DEBUG] 诊断日志，下次运行即可确认）

- [x] 未知版面标签不再被静默跳过：不在 `TEXT_LABELS`、`IMAGE_LABELS`、`table`、`formula` 中的标签被作为正文文本提取

- [x] `TEXT_LABELS` 集合已添加 `list`、`list_item`、`item` 等列表标签

- [x] `NON_BODY_LABELS` 不包含列表相关标签

- [x] `split_translated_result` 提前退出时为剩余块分配原文回退，而非空字符串

- [x] 翻译拆分完整性校验日志已添加：记录空块数量和回退策略

- [x] `extract_pdf_content` 中记录每页提取的文本块数量和 `is_body_text = False` 的块数量

- [x] OCR 提取完成后对比原始页面数和提取结果页面数，记录差异

- [x] `pytest tests/test_ocr_extractor.py` 全部通过（23 passed）

- [x] `pytest tests/test_text_splitting.py` 全部通过（14 passed）

- [ ] 手动测试用户 PDF 确认第四页内容不再丢失（需要用户提供 PDF 文件进行测试）
