## OCR 降级逻辑

- [x] `_degrade_params` 根据 attempt 设置 skip_table/skip_formula
- [x] attempt=0: skip_table=False, skip_formula=False
- [x] attempt=1: skip_table=True, skip_formula=False
- [x] attempt≥2: skip_table=True, skip_formula=True
- [x] test_ocr_worker.py 4个测试通过

## 同语言优化测试

- [x] test_same_language_optimization.py 已删除

## NON_BODY_LABELS

- [x] `header` 已加入 NON_BODY_LABELS
- [x] test_extract_from_pdf_non_body_labels 通过

## OCR 提取器测试

- [x] test_extract_from_pdf_with_table mock 适配单管线架构
- [x] 测试通过

## 语义合并测试

- [x] test_semantic_merge.py 通过
- [x] test_semantic_merge_extended.py 字典访问改为属性访问
- [x] 重复方法已删除
- [x] 6个测试通过

## 标题正文分离测试

- [x] test_title_body_separation.py 适配新逻辑
- [x] 4个测试通过

## 翻译服务集成测试

- [x] test_translation_service.py 参数和 mock 更新
- [x] test_pdf_page_translation.py 参数和 mock 更新
- [x] test_pdf_extractor.py 签名适配
- [x] 7个测试通过

## 系统分析器测试

- [x] test_system_profiler.py tier 边界值修正
- [x] 5个测试通过

## 全量回归

- [x] `pytest --ignore=tests/test_simple_pdf_gen.py` 360 passed, 1 skipped, 0 failed
