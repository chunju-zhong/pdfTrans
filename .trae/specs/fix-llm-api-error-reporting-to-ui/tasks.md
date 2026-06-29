# Tasks

- [x] Task 1: 新建 `modules/llm_error_handler.py` 错误分类工具
  - [x] SubTask 1.1: 从 `openai` 导入 `BadRequestError`、`AuthenticationError`、`RateLimitError`、`APITimeoutError`、`APIConnectionError`、`InternalServerError`
  - [x] SubTask 1.2: 实现 `classify_llm_error(e: Exception) -> dict` 函数，返回 `{'category', 'user_message', 'is_retryable', 'original_message'}`
  - [x] SubTask 1.3: 对 `BadRequestError` 检测 `max_tokens` 关键字，分类为 `bad_request_max_tokens` 并生成含「降低 max_tokens 配置」建议的中文消息
  - [x] SubTask 1.4: 覆盖 6 类 OpenAI 异常 + 通用兜底（`unknown`）

- [x] Task 2: 增强 OCR 调用点错误消息（[modules/ocr/llm_extractor.py](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_extractor.py)）
  - [x] SubTask 2.1: 在 `_extract_page` 的 `except Exception` 块中调用 `classify_llm_error(e)` 替代 `str(e)`
  - [x] SubTask 2.2: 当 `category == 'bad_request_max_tokens'` 时，追加 `（当前 OCR_LLM_MAX_TOKENS={config.OCR_LLM_MAX_TOKENS}）`
  - [x] SubTask 2.3: 确保错误仍通过既有 `progress_callback('page_error', ...)` 上报（不修改上报机制）

- [x] Task 3: 增强翻译调用点错误消息并保留异常类型
  - [x] SubTask 3.1: [modules/silicon_flow_translator.py:87](file:///Users/chunju/work/pdfTrans/modules/silicon_flow_translator.py#L87) 使用 `classify_llm_error` + `raise ... from e`
  - [x] SubTask 3.2: [modules/qianfan_translator.py:89](file:///Users/chunju/work/pdfTrans/modules/qianfan_translator.py#L89) 同上
  - [x] SubTask 3.3: [modules/aiping_translator.py:92](file:///Users/chunju/work/pdfTrans/modules/aiping_translator.py#L92) 同上
  - [x] SubTask 3.4: [modules/translator.py:189](file:///Users/chunju/work/pdfTrans/modules/translator.py#L189) `format_blocks` 异常处理使用 `classify_llm_error`，保留返回原文的降级行为

- [x] Task 4: 增强语义分析调用点错误消息
  - [x] SubTask 4.1: [modules/semantic_analyzer.py:104](file:///Users/chunju/work/pdfTrans/modules/semantic_analyzer.py#L104) `analyze_semantic_relationship` 异常处理使用 `classify_llm_error` 增强 `logger.error`，保留返回 `False` 的降级行为
  - [x] SubTask 4.2: [modules/semantic_analyzer.py:206](file:///Users/chunju/work/pdfTrans/modules/semantic_analyzer.py#L206) `batch_analyze_semantic_relationship` 同上
  - [x] SubTask 4.3: [modules/aiping_semantic_analyzer.py:58](file:///Users/chunju/work/pdfTrans/modules/aiping_semantic_analyzer.py#L58) 同上
  - [x] SubTask 4.4: [modules/aiping_semantic_analyzer.py:168](file:///Users/chunju/work/pdfTrans/modules/aiping_semantic_analyzer.py#L168) 同上

- [x] Task 5: 增强术语提取调用点错误消息
  - [x] SubTask 5.1: [modules/glossary_extractor.py:145](file:///Users/chunju/work/pdfTrans/modules/glossary_extractor.py#L145) 异常处理使用 `classify_llm_error` 增强 `logger.error`，保留返回 `""` 的降级行为

- [x] Task 6: 增强 Markdown 排版调用点错误消息
  - [x] SubTask 6.1: [modules/markdown_generator.py:187](file:///Users/chunju/work/pdfTrans/modules/markdown_generator.py#L187) `_call_api` 异常处理使用 `classify_llm_error`（外层已有 `add_warning` 上报，仅增强消息）
  - [x] SubTask 6.2: [modules/markdown_generator.py:1344](file:///Users/chunju/work/pdfTrans/modules/markdown_generator.py#L1344) aiping `_call_api` 同上

- [x] Task 7: 修复静默吞没点，增加 UI 上报
  - [x] SubTask 7.1: [services/translation_content.py:155-166](file:///Users/chunju/work/pdfTrans/services/translation_content.py#L155) `format_blocks` 调用处增加 `task.add_warning("排版失败，已回退到未排版译文", {"process": "format", "error": friendly_message})`
  - [x] SubTask 7.2: [services/translation_table.py:87-119](file:///Users/chunju/work/pdfTrans/services/translation_table.py#L87) 表格行翻译汇总增加 `task.add_warning("表格行翻译失败，已回退到原文", {"process": "table_translation", "error": friendly_message})`
  - [x] SubTask 7.3: [services/translation_table.py:311-325](file:///Users/chunju/work/pdfTrans/services/translation_table.py#L311) 表格行翻译 fallback 增加 `task.add_warning`
  - [x] SubTask 7.4: [services/glossary_service.py:91-96](file:///Users/chunju/work/pdfTrans/services/glossary_service.py#L91) 术语提取逐页增加 `task.add_warning("术语提取失败，翻译将不使用术语表", {"process": "glossary", "error": friendly_message})`
  - [x] SubTask 7.5: [services/glossary_service.py:130-132](file:///Users/chunju/work/pdfTrans/services/glossary_service.py#L130) 术语提取整体增加 `task.add_warning`

- [x] Task 8: 验证修复效果
  - [x] SubTask 8.1: 运行 `tests/test_llm_ocr.py` 确认现有测试通过
  - [x] SubTask 8.2: 运行其他相关测试（`tests/test_translator.py`、`tests/test_glossary*.py` 等）确认无回归
  - [x] SubTask 8.3: 确认 `paddleocr-vl-0.9b` 触发 400 `max_tokens` 错误时，UI 收到的 `error_msg` 包含友好提示与 `OCR_LLM_MAX_TOKENS` 值

- [x] Task 9: 修复验证发现的 CRITICAL 回归
  - [x] SubTask 9.1: `modules/semantic_analyzer.py` 头部补齐 `from modules.llm_error_handler import classify_llm_error`
  - [x] SubTask 9.2: `modules/aiping_semantic_analyzer.py` 头部补齐 `from modules.llm_error_handler import classify_llm_error`
  - [x] SubTask 9.3: 重跑 `tests/test_semantic_analyzer.py` 确认 11 个测试全部通过

# Task Dependencies
- Task 2-6 依赖 Task 1（需要 `classify_llm_error` 工具）
- Task 7 依赖 Task 2-6（需要调用点已使用 `classify_llm_error`，服务层才能拿到友好消息）
- Task 8 依赖 Task 7（需要全部修改完成）
- Task 2-6 之间无依赖，可并行执行
- Task 9 依赖 Task 8（验证发现回归后修复）

# 验证结果摘要
- `tests/test_llm_ocr.py` 历史失败用例（`OCR_LLM_DPI` 属性缺失、`PdfGenerator._contains_latex_formula` 历史问题）与本 spec 无关
- `tests/test_translator.py`、`test_silicon_flow_translator.py`、`test_qianfan_translator.py` 3 个流式调用测试失败为用户的流式调用改动（`stream=False` → `stream=True`）所致，超出本 spec 范围，不应回滚
- `tests/test_semantic_analyzer.py` 11 个测试全部通过（含修复后的 `test_analyze_semantic_relationship_api_error`）
- `tests/test_glossary_extractor.py`、`test_glossary_extraction.py`、`test_markdown_generator.py` 全部通过
- `classify_llm_error` 6 类异常分类验证全部通过
- `paddleocr-vl-0.9b` 触发 400 `max_tokens` 错误场景验证通过：`error_msg` 包含「max_tokens 参数超限」+「OCR_LLM_MAX_TOKENS=...」
