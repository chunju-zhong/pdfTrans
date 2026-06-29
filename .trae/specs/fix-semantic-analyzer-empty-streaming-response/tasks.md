# Tasks

- [x] Task 1: 改造 `AipingSemanticAnalyzer.analyze_semantic_relationship`（流式单次）的响应处理
  - [x] SubTask 1.1: 在 `modules/aiping_semantic_analyzer.py` 的 `analyze_semantic_relationship` 流式处理段（约第 77-86 行），新增 `reasoning_content_accumulated = ""` 和 `finish_reason = ""` 变量初始化（参考 `aiping_translator.py` 第 114-115 行模式）
  - [x] SubTask 1.2: 将 `elif hasattr(delta, "reasoning_content"): continue` 改为 `elif hasattr(delta, "reasoning_content") and delta.reasoning_content: reasoning_content_accumulated += delta.reasoning_content`（累积而非跳过，参考 `aiping_translator.py` 第 122-124 行）
  - [x] SubTask 1.3: 在流式循环中新增 `finish_reason` 捕获：`if hasattr(choice, "finish_reason") and choice.finish_reason: finish_reason = choice.finish_reason`（参考 `aiping_translator.py` 第 135-138 行）
  - [x] SubTask 1.4: 流式循环结束后、调用 `_extract_json_from_response` 前，新增空结果 fallback 逻辑：若 `not analysis_result`（content 为空），记录 WARNING 日志（含 reasoning_content_accumulated 长度、finish_reason、text1/text2 前 100 字符），并将 `reasoning_content_accumulated` 作为 fallback 传给 `_extract_json_from_response`；若 fallback 也返回 None，才走原有 `raise json.JSONDecodeError` 逻辑

- [x] Task 2: 改造 `AipingSemanticAnalyzer.batch_analyze_semantic_relationship`（流式批量）的响应处理
  - [x] SubTask 2.1: 在 `modules/aiping_semantic_analyzer.py` 的 `batch_analyze_semantic_relationship` 流式处理段（约第 168-184 行），新增 `reasoning_content_accumulated = ""` 和 `finish_reason = ""` 变量初始化
  - [x] SubTask 2.2: 将 `elif hasattr(delta, "reasoning_content"): continue`（含 debug 日志的版本）改为累积 `reasoning_content_accumulated`，保留 debug 日志但改为记录累积长度
  - [x] SubTask 2.3: 在流式循环中新增 `finish_reason` 捕获（同 Task 1.3）
  - [x] SubTask 2.4: 流式循环结束后、调用 `_extract_json_from_response` 前，新增空结果 fallback 逻辑：若 `not analysis_result`，记录 WARNING 日志（含 reasoning_content_accumulated 长度、finish_reason、blocks 数量、blocks[0] 前 100 字符），将 `reasoning_content_accumulated` 作为 fallback 传给 `_extract_json_from_response`；若 fallback 也返回 None，才走原有 `raise json.JSONDecodeError` 逻辑

- [x] Task 3: 验证修复效果
  - [x] SubTask 3.1: 编写单元测试：模拟 content 为空、reasoning_content 含 `{"merge": true}` 的流式响应，验证单次分析返回 True 且不触发重试
  - [x] SubTask 3.2: 编写单元测试：模拟 content 为空、reasoning_content 含 `{"merge": [true, false]}` 的流式响应，验证批量分析返回 `[True, False]` 且不触发重试
  - [x] SubTask 3.3: 编写单元测试：模拟 content 和 reasoning_content 均为空的流式响应，验证 WARNING 日志记录且走原有重试/默认值逻辑
  - [x] SubTask 3.4: 运行现有语义分析器测试（`tests/test_semantic_analyzer.py`、`tests/test_semantic_analyzer_json_extraction.py`、`tests/test_batch_semantic_analysis.py`），确保无回归

# Task Dependencies

- Task 2 与 Task 1 独立（同一文件不同方法，可并行但建议顺序以避免编辑冲突）
- Task 3 依赖 Task 1 和 Task 2 完成
