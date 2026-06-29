# Checklist

## 新增工具模块
- [x] `modules/llm_error_handler.py` 存在且导出 `classify_llm_error(e: Exception) -> dict` 函数
- [x] `classify_llm_error` 返回的 dict 包含 `category`、`user_message`、`is_retryable`、`original_message` 四个字段
- [x] 覆盖 `AuthenticationError`（401）→ `category='auth'`
- [x] 覆盖 `RateLimitError`（429）→ `category='rate_limit'`，`is_retryable=True`
- [x] 覆盖 `BadRequestError` 含 `max_tokens` → `category='bad_request_max_tokens'`，消息含「降低 max_tokens 配置」建议
- [x] 覆盖 `BadRequestError` 其他 → `category='bad_request'`
- [x] 覆盖 `APITimeoutError` → `category='timeout'`，`is_retryable=True`
- [x] 覆盖 `APIConnectionError` → `category='connection'`，`is_retryable=True`
- [x] 覆盖 `InternalServerError`（5xx）→ `category='server_error'`，`is_retryable=True`
- [x] 覆盖未知异常 → `category='unknown'`，`original_message` 保留 `str(e)`
- [x] 所有 `user_message` 为中文用户友好消息

## OCR 调用点（modules/ocr/llm_extractor.py）
- [x] `_extract_page` 的 `except Exception` 块使用 `classify_llm_error(e)` 替代 `str(e)`
- [x] 当 `category == 'bad_request_max_tokens'` 时，`error_msg` 追加 `（当前 OCR_LLM_MAX_TOKENS={config.OCR_LLM_MAX_TOKENS}）`
- [x] 错误仍通过 `progress_callback('page_error', ...)` 上报（机制未修改）
- [x] `APITimeoutError` 仍走既有超时处理分支（含重试），未被影响
- [x] `config.OCR_LLM_MAX_TOKENS` 默认值未修改

## 翻译调用点
- [x] `modules/silicon_flow_translator.py:5` 导入 `classify_llm_error`，异常处理使用 `raise ... from e`
- [x] `modules/qianfan_translator.py:5` 导入 `classify_llm_error`，异常处理使用 `raise ... from e`
- [x] `modules/aiping_translator.py:5` 导入 `classify_llm_error`，异常处理使用 `raise ... from e`
- [x] `modules/translator.py:5` 导入 `classify_llm_error`，`format_blocks` 异常处理增强 `logger.warning`，保留返回原文降级行为

## 语义分析调用点
- [x] `modules/semantic_analyzer.py:4` 导入 `classify_llm_error`，`analyze_semantic_relationship` 异常处理增强 `logger.error`，保留返回 `False` 降级行为
- [x] `modules/semantic_analyzer.py` `batch_analyze_semantic_relationship` 同上
- [x] `modules/aiping_semantic_analyzer.py:3` 导入 `classify_llm_error`，单分析异常处理增强
- [x] `modules/aiping_semantic_analyzer.py` 批量分析异常处理增强
- [x] `tests/test_semantic_analyzer.py` 11 个测试全部通过（含修复后的 `test_analyze_semantic_relationship_api_error`）

## 术语提取调用点
- [x] `modules/glossary_extractor.py:4` 导入 `classify_llm_error`，异常处理增强 `logger.error`，保留返回 `""` 降级行为

## Markdown 排版调用点
- [x] `modules/markdown_generator.py:9` 导入 `classify_llm_error`，`_call_api` 异常处理增强错误消息
- [x] `modules/markdown_generator.py` aiping `_call_api` 同上
- [x] 外层 `MarkdownGenerationResult.add_warning` 上报机制未修改

## 静默吞没点 UI 上报
- [x] `services/translation_content.py:155-166` `format_blocks` 失败时调用 `task.add_warning("排版失败，已回退到未排版译文", ...)`
- [x] `services/translation_table.py:87-119` 表格行翻译失败时调用 `task.add_warning("表格行翻译失败，已回退到原文", ...)`
- [x] `services/translation_table.py:311-325` 表格行翻译 fallback 调用 `task.add_warning`
- [x] `services/glossary_service.py:91-96` 术语提取逐页失败时调用 `task.add_warning("术语提取失败，翻译将不使用术语表", ...)`（含 `if task:` 守卫）
- [x] `services/glossary_service.py:130-132` 术语提取整体失败时调用 `task.add_warning`
- [x] 所有 `task.add_warning` 的 `context` 字典包含 `error` 字段（友好消息）

## 不变项验证
- [x] `config.py` 中 `OCR_LLM_MAX_TOKENS`、`GLOSSARY_MAX_TOKENS`、`LAYOUT_MAX_TOKENS` 默认值未修改
- [x] API 调用参数（`max_tokens`、`temperature` 等）未被钳制或修改
- [x] prompt 构建、`extra_body` 逻辑未修改
- [x] 已正确上报 UI 的调用点（`process_merged_blocks`、`process_original_blocks`、`translation_extractor`）机制未修改

## 测试验证
- [x] `tests/test_llm_ocr.py` 现有测试通过（历史失败用例与本 spec 无关）
- [x] `tests/test_semantic_analyzer.py` 11 个测试全部通过（含修复后的 API 错误测试）
- [x] `tests/test_glossary_extractor.py`、`test_glossary_extraction.py`、`test_markdown_generator.py` 全部通过
- [x] `classify_llm_error` 6 类异常分类全部验证通过（max_tokens、auth、rate_limit、bad_request、timeout、unknown）
- [x] `paddleocr-vl-0.9b` 触发 400 `max_tokens` 错误时，UI 收到的 `error_msg` 包含友好提示与 `OCR_LLM_MAX_TOKENS` 值
- [x] 修复 `semantic_analyzer.py` 与 `aiping_semantic_analyzer.py` 缺失 import 的 CRITICAL 回归

## 范围外说明
- `tests/test_translator.py`、`test_silicon_flow_translator.py`、`test_qianfan_translator.py` 3 个流式调用测试失败为用户的流式调用改动（`stream=False` → `stream=True`）所致，超出本 spec 范围，根据规则不应回滚
- `tests/test_llm_ocr.py::TestLlmOcrConfigDefaults` 与 `TestMixedFormulaTextRendering` 失败为历史问题（`OCR_LLM_DPI` 属性缺失、`PdfGenerator._contains_latex_formula` 历史问题），与本 spec 无关
