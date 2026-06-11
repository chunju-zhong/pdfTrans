# Tasks

- [x] Task 1: _merge_batch_results 返回缺失页码信息
  - [x] SubTask 1.1: `_merge_batch_results` 函数签名新增 `all_page_nums` 参数
  - [x] SubTask 1.2: 计算缺失页码 = all_page_nums 中不在任何 valid_result.pages 中的页码
  - [x] SubTask 1.3: 返回值从 `PdfExtraction` 改为 `(PdfExtraction, list[int])` 元组

- [x] Task 2: PdfExtractor.extract 适配新返回值
  - [x] SubTask 2.1: OCR 分批路径调用 `_merge_batch_results(all_results, all_page_nums)` 并解构元组
  - [x] SubTask 2.2: OCR 单批路径返回 `(result, [])`
  - [x] SubTask 2.3: 非 OCR 路径收集 `_process_page` 返回 None 的页码到 `failed_pages`，返回 `(result, failed_pages)`
  - [x] SubTask 2.4: 非 OCR 路径所有返回语句统一返回元组格式

- [x] Task 3: translation_service 检查提取完整性并添加警告
  - [x] SubTask 3.1: 适配 `extract()` 返回的元组：`extracted_content, missing_pages = pdf_extractor.extract(...)`
  - [x] SubTask 3.2: `missing_pages` 非空时调用 `task.add_warning()` 通知用户
  - [x] SubTask 3.3: `missing_pages` 包含所有目标页面时返回 None（全部失败）
  - [x] SubTask 3.4: "页面无正文块"的 `logger.warning` 改为同时调用 `task.add_warning()`
  - [x] SubTask 3.5: 检查 `process_translation_sync` 中的 `extract()` 调用也适配新返回值

- [x] Task 4: glossary_service.py 适配 extract() 新返回值
  - [x] SubTask 4.1: 第270行 `extraction_result = pdf_extractor.extract(...)` → `extraction_result, _ = pdf_extractor.extract(...)`
  - [x] SubTask 4.2: 第347行 `extraction_result = pdf_extractor.extract([page_num])` → `extraction_result, _ = pdf_extractor.extract([page_num])`

# Task Dependencies
- Task 1 → Task 2 → Task 3 顺序执行
- Task 4 独立，与 Task 3 并行
