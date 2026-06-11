# Tasks

- [x] Task 1: 修复 `_degrade_params` 降级逻辑（4个测试）
  - [x] SubTask 1.1: 在 `_degrade_params` 中根据 `attempt` 设置 `skip_table` 和 `skip_formula`
  - [x] SubTask 1.2: 统一降级策略（attempt=0 也降一级线程数/DPI），使测试与代码一致
  - [x] SubTask 1.3: 运行 `pytest tests/test_ocr_worker.py -v` 验证

- [x] Task 2: 删除 `test_same_language_optimization.py`（4个测试）
  - [x] SubTask 2.1: 删除 `tests/test_same_language_optimization.py`（`handle_same_language` 已有意移除）
  - [x] SubTask 2.2: 确认无其他文件引用该测试

- [x] Task 3: `NON_BODY_LABELS` 增加 `header`（1个测试）
  - [x] SubTask 3.1: 在 `paddle_extractor.py` 的 `NON_BODY_LABELS` 中加入 `header`
  - [x] SubTask 3.2: 运行 `pytest tests/test_ocr_extractor.py::TestPaddleOcrExtractor::test_extract_from_pdf_non_body_labels -v` 验证

- [x] Task 4: 更新 `test_ocr_extractor.py` 的 mock 策略（1个测试）
  - [x] SubTask 4.1: 修改 `test_extract_from_pdf_with_table` 适配单管线架构
  - [x] SubTask 4.2: 运行 `pytest tests/test_ocr_extractor.py::TestPaddleOcrExtractor::test_extract_from_pdf_with_table -v` 验证

- [x] Task 5: 修复语义合并测试（6个测试）
  - [x] SubTask 5.1: `test_semantic_merge_extended.py` 字典访问改为属性访问 + 删除重复方法
  - [x] SubTask 5.2: 运行 `pytest tests/test_semantic_merge.py tests/test_semantic_merge_extended.py -v` 验证

- [x] Task 6: 修复标题正文分离测试（4个测试）
  - [x] SubTask 6.1: `test_title_body_separation.py` — 适配 `TextBlock` 构造函数签名和 `merge_semantic_blocks` 新逻辑
  - [x] SubTask 6.2: 运行 `pytest tests/test_title_body_separation.py -v` 验证

- [x] Task 7: 修复翻译服务集成测试（7个测试）
  - [x] SubTask 7.1: `test_translation_service.py` — 更新 `process_translation` 参数和 mock 链条
  - [x] SubTask 7.2: `test_pdf_page_translation.py` — 更新参数和 mock 链条
  - [x] SubTask 7.3: `test_pdf_extractor.py` — 适配 `PdfExtractor` 签名变更
  - [x] SubTask 7.4: 运行 `pytest tests/test_translation_service.py tests/test_pdf_page_translation.py tests/test_pdf_extractor.py -v` 验证

- [x] Task 8: 修复系统分析器测试（5个测试）
  - [x] SubTask 8.1: `test_system_profiler.py` — 修正 `OcrParameterCalculator` tier 边界值
  - [x] SubTask 8.2: 运行 `pytest tests/test_system_profiler.py -v` 验证

- [x] Task 9: 全量回归验证
  - [x] SubTask 9.1: 运行 `pytest --ignore=tests/test_simple_pdf_gen.py -v` 确认 0 失败

# Task Dependencies

- [Task 5], [Task 6] 可并行
- [Task 7] 依赖 [Task 5]
- [Task 9] 依赖所有其他 Task
