# Tasks

- [x] Task 1: 添加 OCR 版面标签诊断日志，确认 PaddleOCR 实际返回的标签
  - [x] SubTask 1.1: 在 `_process_page_layout` 中记录所有 PaddleOCR 返回的版面标签（包括不在 `TEXT_LABELS` 中的标签）及对应文本内容
  - [x] SubTask 1.2: 对用户提供的 PDF 运行 OCR 提取，检查第四页的标签分布，确认 "Overflow surface load" 内容的标签类型
  - [x] SubTask 1.3: 记录被跳过的标签及数量，输出警告级别日志

- [x] Task 2: 修复 `TEXT_LABELS` 集合遗漏问题，将未知标签视为正文文本
  - [x] SubTask 2.1: 在 `_process_page_layout` 中，对不在 `TEXT_LABELS`、`IMAGE_LABELS`、`table`、`formula` 中的标签，记录警告日志并将其作为正文文本块提取
  - [x] SubTask 2.2: 将 `list`、`list_item`、`item` 等常见列表标签添加到 `TEXT_LABELS` 集合
  - [x] SubTask 2.3: 确保 `NON_BODY_LABELS` 不包含列表相关标签

- [x] Task 3: 修复 `split_translated_result` 提前退出导致后续块内容丢失
  - [x] SubTask 3.1: 当翻译文本耗尽时，不再提前退出，而是为剩余块分配原文作为回退
  - [x] SubTask 3.2: 添加翻译拆分完整性校验日志，记录空块数量和回退策略

- [x] Task 4: 添加提取阶段内容完整性校验
  - [x] SubTask 4.1: 在 `extract_pdf_content` 中，记录每页提取的文本块数量和 `is_body_text = False` 的块数量
  - [x] SubTask 4.2: 在 OCR 提取完成后，对比原始页面数和提取结果页面数，记录差异

- [x] Task 5: 运行测试验证修复
  - [x] SubTask 5.1: 运行 `pytest tests/test_ocr_extractor.py` 确保现有测试通过（23 passed）
  - [x] SubTask 5.2: 运行 `pytest tests/test_text_splitting.py` 确保拆分逻辑正确（14 passed）
  - [ ] SubTask 5.3: 手动测试用户提供的 PDF，确认第四页内容不再丢失

# Task Dependencies

- Task 1 无依赖，可直接开始（诊断优先）
- Task 2 依赖于 Task 1 的诊断结果确认标签类型
- Task 3 无依赖，可与 Task 1 并行
- Task 4 无依赖，可与 Task 1 并行
- Task 5 依赖于 Task 2、Task 3、Task 4 完成
