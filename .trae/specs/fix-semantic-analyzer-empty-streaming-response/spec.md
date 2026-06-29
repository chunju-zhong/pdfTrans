# 修复语义分析器流式响应空结果 Spec

## Why

`AipingSemanticAnalyzer` 的流式响应处理代码（`modules/aiping_semantic_analyzer.py` 第 77-86 行单次、第 168-184 行批量）在处理 LLM 流式响应时，只收集 `delta.content`，对 `delta.reasoning_content` 直接 `continue` 跳过，且不记录任何诊断信息。当 Qwen3-32B 模型（经 aiping 平台路由）尽管配置了 `enable_thinking: False`，仍将回复输出在 `reasoning_content` 中（或因 `max_tokens` 耗尽在思考阶段，未产出 `content`）时，`analysis_result` 保持为空字符串 `''`，`_extract_json_from_response('')` 返回 `None`，触发 `JSONDecodeError`，3 次重试全部失败，最终回退到全 `False` 默认值，语义合并完全失效。

此问题与已完成的 `fix-page18-text-not-translated` spec 同源（Qwen3 思考模式导致 `content` 为空），但该修复仅应用于 `aiping_translator.py`，未覆盖 `aiping_semantic_analyzer.py`。

错误日志证据：
```
2026-06-27 10:57:06,837 - modules.aiping_semantic_analyzer - ERROR - JSON解析错误: 无法从响应中提取JSON: line 1 column 1 (char 0)
2026-06-27 10:57:06,839 - modules.aiping_semantic_analyzer - ERROR - 无法解析的原始结果: ''
```
原始结果为空字符串 `''`，且无任何诊断信息（不知道是否有 `reasoning_content`、`finish_reason` 是什么），无法定位是思考内容泄露还是 `max_tokens` 截断。

## What Changes

- `AipingSemanticAnalyzer.analyze_semantic_relationship`（流式单次，`modules/aiping_semantic_analyzer.py`）：
  - 新增 `reasoning_content_accumulated` 变量，累积 `delta.reasoning_content` 文本（不再仅 `continue` 跳过）
  - 新增 `finish_reason` 变量，从流式 chunk 的 `choices[0].finish_reason` 捕获
  - 流式处理完毕后，若 `analysis_result`（content）为空：
    - 记录 WARNING 日志，包含 `reasoning_content_accumulated` 长度、`finish_reason`、文本块前 100 字符
    - 将 `reasoning_content_accumulated` 作为 fallback 传给 `_extract_json_from_response` 尝试提取 JSON
    - 若 fallback 仍返回 `None`，才走原有 `raise json.JSONDecodeError` 逻辑
- `AipingSemanticAnalyzer.batch_analyze_semantic_relationship`（流式批量，同文件）：同上改造
- 参考实现：`modules/aiping_translator.py` 第 112-147 行（`fix-page18-text-not-translated` 已建立的模式），但额外增加 `reasoning_content` 文本累积与 JSON 提取 fallback（translator 不需要此 fallback 因为翻译结果非 JSON）

## Impact

- Affected specs:
  - `fix-page18-text-not-translated`（同源问题，本次扩展至语义分析器）
  - `fix-semantic-analyzer-json-fence-parsing`（前置修复，本次复用其 `_extract_json_from_response` 方法作为 fallback 提取器）
- Affected code:
  - `modules/aiping_semantic_analyzer.py` — 修改 `analyze_semantic_relationship` 和 `batch_analyze_semantic_relationship` 的流式响应处理段

## ADDED Requirements

### Requirement: 语义分析器流式响应思考内容累积与诊断

系统 SHALL 在 `AipingSemanticAnalyzer` 流式响应处理中，累积 `reasoning_content` 文本并捕获 `finish_reason`，当 `content` 为空时记录诊断日志并尝试从 `reasoning_content` 提取 JSON。

#### Scenario: 模型正常返回 content（无思考内容）
- **WHEN** 流式响应的 `delta.content` 有内容
- **THEN** SHALL 累积到 `analysis_result`
- **AND** SHALL 不触发 fallback 逻辑

#### Scenario: 模型仅在 reasoning_content 中输出 JSON（思考模式泄露）
- **WHEN** 流式响应的 `delta.content` 为空或 None，但 `delta.reasoning_content` 包含内容
- **THEN** SHALL 累积 `reasoning_content` 到 `reasoning_content_accumulated`
- **AND** 流式结束后若 `analysis_result` 为空，SHALL 记录 WARNING 日志（含 reasoning_content 长度、finish_reason）
- **AND** SHALL 将 `reasoning_content_accumulated` 传给 `_extract_json_from_response` 尝试提取 JSON
- **AND** 若提取成功，SHALL 正常返回合并决策（不触发重试）

#### Scenario: content 和 reasoning_content 均为空
- **WHEN** 流式响应既无 `content` 也无 `reasoning_content`（如 API 返回空、rate limit）
- **THEN** SHALL 记录 WARNING 日志（reasoning_content长度=0, finish_reason）
- **AND** SHALL 走原有 `raise json.JSONDecodeError` 逻辑，触发重试或默认值

#### Scenario: 捕获 finish_reason 用于诊断
- **WHEN** 流式 chunk 的 `choices[0].finish_reason` 存在
- **THEN** SHALL 捕获到最后一个非空 `finish_reason`
- **AND** 当 `content` 为空时，SHALL 在 WARNING 日志中输出 `finish_reason`（如 `length` 表示 max_tokens 截断）

## MODIFIED Requirements

### Requirement: AipingSemanticAnalyzer 流式响应处理

`AipingSemanticAnalyzer.analyze_semantic_relationship` 与 `batch_analyze_semantic_relationship` SHALL 在流式响应处理中累积 `reasoning_content` 并在 `content` 为空时 fallback 到 `reasoning_content` 提取 JSON。

#### Scenario: 单次分析 content 为空但 reasoning_content 含 JSON
- **WHEN** 流式响应 content 为空，reasoning_content 含 `{"merge": true}`
- **THEN** SHALL 从 reasoning_content 提取 JSON 并返回 `True`
- **AND** SHALL 不触发重试

#### Scenario: 批量分析 content 为空但 reasoning_content 含 JSON 数组
- **WHEN** 流式响应 content 为空，reasoning_content 含 `{"merge": [true, false, true]}`
- **THEN** SHALL 从 reasoning_content 提取 JSON 并返回 `[True, False, True]`
- **AND** SHALL 不触发重试

#### Scenario: 单次/批量分析 content 和 reasoning_content 均无 JSON
- **WHEN** content 和 reasoning_content 都无法提取到 JSON
- **THEN** SHALL 记录 WARNING 诊断日志
- **AND** SHALL 走原有重试/默认值逻辑（保持 `fix-semantic-analyzer-json-fence-parsing` 的行为不变）
