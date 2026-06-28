# 修复硅基流动/百度千帆空响应处理与诊断 Spec

## Why

调查 `fix-semantic-analyzer-empty-streaming-response` 修复后的同源问题时发现，硅基流动（SiliconFlow）和百度千帆（Qianfan）虽然使用非流式调用（`stream=False`），不存在流式 `reasoning_content` 跳过的同源问题，但存在 3 个潜在缺陷，会在未来切换到 thinking 模型（如 Qwen3-32B）或遇到空响应时静默失败：

1. **`SiliconFlowTranslator` 和 `QianfanTranslator` 未传 `extra_body`**：`client.chat.completions.create` 调用中没有 `extra_body` 参数，导致 `enable_thinking: False` 配置未生效。当前默认模型（`tencent/Hunyuan-MT-7B`）不支持 thinking 所以无问题，但切换到 Qwen3-32B 等 thinking 模型会触发非流式响应中 `message.content` 为空而 `message.reasoning_content` 有内容的情况。
2. **`SiliconFlowTranslator` 和 `QianfanTranslator` 缺少空结果诊断日志**：读取 `choice.message.content.strip()` 后无 WARNING 日志，翻译结果为空时静默返回空字符串，无诊断信息（对比 `aiping_translator.py` 第 141-147 行已建立的模式）。
3. **`SemanticAnalyzer` 基类缺少空结果诊断与 fallback**：基类的 `analyze_semantic_relationship`（第 124-126 行）和 `batch_analyze_semantic_relationship`（第 207-211 行）直接读取 `message.content.strip()`，无 WARNING 日志、无 fallback 到 `message.reasoning_content`。silicon_flow 和 qianfan 语义分析器使用基类，遇到空 content 时直接走 `JSONDecodeError` 重试路径，无诊断信息。

## What Changes

- `SiliconFlowTranslator.translate`（`modules/silicon_flow_translator.py`）：
  - 在 `client.chat.completions.create` 调用中补传 `extra_body=config.SILICON_FLOW_EXTRA_BODY`
  - 补传 `max_tokens=self.max_tokens`（`self.max_tokens` 已在 `__init__` 中设置但未传入 API 调用）
  - 读取 `choice.message.content` 后，添加空结果 WARNING 诊断日志（含 finish_reason、原文前 100 字符）
  - 当 content 为空时，fallback 读取 `choice.message.reasoning_content`（如有）
- `QianfanTranslator.translate`（`modules/qianfan_translator.py`）：同上改造，`extra_body` 使用 `config.QIANFAN_EXTRA_BODY`
- `SemanticAnalyzer.analyze_semantic_relationship`（`modules/semantic_analyzer.py` 第 102-127 行）：添加空结果 WARNING 诊断日志，content 为空时 fallback 读取 `message.reasoning_content`
- `SemanticAnalyzer.batch_analyze_semantic_relationship`（`modules/semantic_analyzer.py` 第 183-215 行）：同上改造
- 参考实现：
  - `aiping_translator.py` 第 112-147 行（流式诊断模式）
  - `aiping_semantic_analyzer.py` 第 96-103 行（流式 fallback 模式）
  - 本次适配为**非流式**版本：直接读 `message.content` / `message.reasoning_content`，无需累积

## Impact

- Affected specs:
  - `fix-page18-text-not-translated`（aiping translator 诊断模式，本次扩展至硅基/千帆 translator）
  - `fix-semantic-analyzer-empty-streaming-response`（aiping semantic analyzer 流式 fallback，本次扩展至基类非流式 fallback）
- Affected code:
  - `modules/silicon_flow_translator.py` — 修改 `translate` 方法的 API 调用与响应处理
  - `modules/qianfan_translator.py` — 同上
  - `modules/semantic_analyzer.py` — 修改基类的 `analyze_semantic_relationship` 和 `batch_analyze_semantic_relationship` 响应处理段
- 不影响 `AipingSemanticAnalyzer`（已重写两个方法，不调用基类实现）
- 不影响 `AipingTranslator`（已建立诊断模式）

## ADDED Requirements

### Requirement: 硅基/千帆 translator 显式传递 extra_body 与 max_tokens

系统 SHALL 在 `SiliconFlowTranslator.translate` 和 `QianfanTranslator.translate` 的 `client.chat.completions.create` 调用中显式传递 `extra_body`（分别为 `config.SILICON_FLOW_EXTRA_BODY` 和 `config.QIANFAN_EXTRA_BODY`）和 `max_tokens=self.max_tokens`，确保 `enable_thinking: False` 配置生效。

#### Scenario: 切换到 thinking 模型时配置生效
- **WHEN** 用户将 SILICON_FLOW_MODEL_TRANSLATION 环境变量改为 Qwen3-32B
- **THEN** SHALL 在 API 调用中传递 `enable_thinking: False`
- **AND** 模型应返回 content 字段（而非 reasoning_content）

### Requirement: 硅基/千帆 translator 空响应诊断与 fallback

系统 SHALL 在 `SiliconFlowTranslator.translate` 和 `QianfanTranslator.translate` 中，当 `translated_text` 为空时记录 WARNING 诊断日志，并尝试从 `choice.message.reasoning_content` 读取 fallback 内容。

#### Scenario: 非流式响应 content 为空但 reasoning_content 有内容
- **WHEN** API 返回 `choice.message.content` 为空或 None，但 `choice.message.reasoning_content` 包含翻译内容
- **THEN** SHALL 记录 WARNING 日志（含 finish_reason、原文前 100 字符）
- **AND** SHALL 将 `reasoning_content` 作为 fallback 赋给 `translated_text`
- **AND** SHALL 正常返回翻译结果（不抛异常）

#### Scenario: content 和 reasoning_content 均为空
- **WHEN** API 返回 `message.content` 和 `message.reasoning_content` 均为空
- **THEN** SHALL 记录 WARNING 日志（含 finish_reason、原文前 100 字符）
- **AND** SHALL 返回空 TranslationResult（保持原有行为）

### Requirement: SemanticAnalyzer 基类空响应诊断与 fallback

系统 SHALL 在 `SemanticAnalyzer.analyze_semantic_relationship` 和 `batch_analyze_semantic_relationship` 中，当 `analysis_result` 为空时记录 WARNING 诊断日志，并尝试从 `message.reasoning_content` 读取 fallback 内容。

#### Scenario: 基类单次分析 content 为空但 reasoning_content 含 JSON
- **WHEN** API 返回 `message.content` 为空，但 `message.reasoning_content` 含 `{"merge": true}`
- **THEN** SHALL 记录 WARNING 日志（含 finish_reason、文本块前 100 字符）
- **AND** SHALL 将 `reasoning_content` 作为 fallback 赋给 `analysis_result`
- **AND** SHALL 正常解析 JSON 并返回合并决策（不触发重试）

#### Scenario: 基类批量分析 content 为空但 reasoning_content 含 JSON 数组
- **WHEN** API 返回 `message.content` 为空，但 `message.reasoning_content` 含 `{"merge": [true, false, true]}`
- **THEN** SHALL 记录 WARNING 日志（含 finish_reason、blocks 数量、blocks[0] 前 100 字符）
- **AND** SHALL 将 `reasoning_content` 作为 fallback 赋给 `analysis_result`
- **AND** SHALL 正常解析 JSON 并返回合并决策列表（不触发重试）

#### Scenario: 基类 content 和 reasoning_content 均为空
- **WHEN** API 返回 `message.content` 和 `message.reasoning_content` 均为空
- **THEN** SHALL 记录 WARNING 日志
- **AND** SHALL 走原有 `raise json.JSONDecodeError` 逻辑（单次返回 False，批量走重试或返回默认值列表）

## MODIFIED Requirements

### Requirement: SiliconFlowTranslator API 调用参数

`SiliconFlowTranslator.translate` SHALL 在 `client.chat.completions.create` 调用中传递 `extra_body=config.SILICON_FLOW_EXTRA_BODY`、`max_tokens=self.max_tokens`、`temperature`、`top_p`，与 `AipingTranslator` 保持参数一致。

### Requirement: QianfanTranslator API 调用参数

`QianfanTranslator.translate` SHALL 在 `client.chat.completions.create` 调用中传递 `extra_body=config.QIANFAN_EXTRA_BODY`、`max_tokens=self.max_tokens`、`temperature`、`top_p`，与 `AipingTranslator` 保持参数一致。

### Requirement: SemanticAnalyzer 基类响应处理

`SemanticAnalyzer.analyze_semantic_relationship` 和 `batch_analyze_semantic_relationship` SHALL 在读取 `message.content` 后，当结果为空时记录 WARNING 诊断日志并 fallback 到 `message.reasoning_content`，与 `AipingSemanticAnalyzer` 流式 fallback 模式对应（非流式版本）。
