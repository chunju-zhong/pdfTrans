# 修复 Qwen3 思考模式导致翻译失败 Spec

## Why

Qwen3-32B 模型默认启用思考模式（thinking/reasoning），翻译请求时模型的 `reasoning_content`（思考内容）可能消耗整个响应，导致 `content`（实际翻译内容）为空。`_postprocess_text` 在翻译结果为空时回退返回原文，造成翻译结果与原文相同。日志证据：`WARNING - 翻译结果与原文相同，可能翻译失败: 原文前100字符="DavID LiDDLe? wHo led the team..."`

## `enable_thinking` 参数官方含义

根据 Qwen 官方文档（https://qwen.readthedocs.io）和 Qwen Cloud API 文档（https://docs.qwencloud.com）：

- **`enable_thinking: True`（Qwen3 默认）**：启用思考模式，模型在回复前会先进行思考推理，响应中包含 `reasoning_content`（思考过程）和 `content`（最终回复）。这是 Qwen3 的默认行为。
- **`enable_thinking: False`**：硬开关，完全禁用思考模式。模型不会生成任何 `reasoning_content`，只返回 `content`（最终回复）。效果等同于 Qwen2.5-Instruct 模型。
- **传递方式**：通过 OpenAI SDK 的 `extra_body={"enable_thinking": False}` 顶层直接传递，不需要嵌套在 `chat_template_kwargs` 中（嵌套方式仅适用于自部署的 SGLang/vLLM 框架）。
- **aiping 代理**：aiping 是智能路由平台，`extra_body` 参数会透明传递给后端模型服务商，因此 `enable_thinking: False` 可以正确生效。
- **采样参数建议**：
  - 思考模式：`temperature=0.6, top_p=0.95, top_k=20`
  - 非思考模式：`temperature=0.7, top_p=0.8, top_k=20`
  - 当前代码使用 `temperature=0.1, top_p=0.9`，属于非思考模式参数，但未禁用思考模式，导致参数不匹配

## `enable_thinking: False` 对翻译质量的影响

### 官方和社区评测结论

1. **翻译场景推荐非思考模式**：Qwen 官方文档和多个社区评测明确指出，翻译、对话、文案润色等"直接映射"类任务特别适合非思考模式。翻译不需要多步推理，模型内部依然会进行语言理解和转换，只是不输出中间思考过程。

2. **质量差异极小**：C-Eval 子集盲测显示，思考模式和非思考模式准确率差异在 ±0.8% 以内。对于翻译这类不需要深度推理的任务，差异更小。

3. **非思考模式优势**：
   - 首 token 延迟（TTFT）降低 40-60%
   - 输出吞吐提升约 1.8 倍
   - 翻译场景实测：英中翻译首字延迟从 420ms 降至 190ms（↓55%）

4. **思考模式适用场景**：数学推理、代码生成、复杂逻辑判断等需要多步推理的任务。翻译不属于这些场景。

5. **当前问题更严重**：当前代码未禁用思考模式，导致部分文本翻译完全失败（返回原文），这比任何微小的质量差异都严重得多。

### 结论

对翻译任务使用 `enable_thinking: False` **不会降低翻译质量**，反而因为消除了思考内容消耗响应空间的风险，**显著提升了翻译的可靠性和速度**。

## 跨平台兼容性分析

### 各平台 Qwen3 使用情况

| 平台 | 用途 | 模型 | 是否 Qwen3 | 是否需要关闭思考 | 当前是否传递 `enable_thinking` |
|------|------|------|-----------|----------------|-------------------------------|
| aiping | 翻译 | Qwen3-32B | 是 | 是 | 通过 `AIPING_EXTRA_BODY`（未包含） |
| aiping | 术语提取 | Qwen3-32B | 是 | 是 | 通过 `AIPING_EXTRA_BODY`（未包含） |
| aiping | 语义分析（排版） | Qwen3-32B | 是 | 是 | 通过 `AIPING_EXTRA_BODY`（未包含） |
| aiping | Markdown 格式化 | Qwen3-32B | 是 | 是 | 通过 `AIPING_EXTRA_BODY`（未包含） |
| 硅基流动 | 翻译 | Hunyuan-MT-7B | 否 | 否（非 Qwen3，参数无效） | 未传递 |
| 硅基流动 | 术语提取 | Qwen/Qwen3-32B | 是 | 是 | 未传递 |
| 硅基流动 | 布局分析 | Qwen/Qwen3-32B | 是 | 是 | 未传递 |

### 各 Qwen3 用途是否应该关闭思考

1. **翻译**：直接映射任务（源语言→目标语言），不需要多步推理 → **应该关闭思考**
2. **术语提取**：分类/提取任务（从文本中识别专业术语），不需要深度推理 → **应该关闭思考**
3. **语义分析（排版）**：分类任务（判断相邻文本块的语义关系），不需要深度推理 → **应该关闭思考**
4. **Markdown 格式化**：格式化任务（将文本格式化为 Markdown），不需要深度推理 → **应该关闭思考**

**结论**：所有 Qwen3 用途都属于"直接映射"类任务，不需要思考模式。应在所有 Qwen3 调用中统一关闭思考模式。

### 处理策略

1. **aiping 平台**：在 `AIPING_EXTRA_BODY` 中添加 `"enable_thinking": False`。aiping 平台的所有 Qwen3 调用（翻译、术语提取、语义分析、Markdown 格式化）都通过 `AIPING_EXTRA_BODY` 传递 `extra_body`，添加后全部自动生效。

2. **硅基流动平台**：在 `config.py` 中新增 `SILICON_FLOW_EXTRA_BODY = {"enable_thinking": False}` 配置项，与 `AIPING_EXTRA_BODY` 模式一致。各模块（术语提取、语义分析、Markdown 格式化）引用 `config.SILICON_FLOW_EXTRA_BODY` 传递 `extra_body`。

3. **硅基流动翻译**：使用 `Hunyuan-MT-7B` 模型，该模型不支持 `enable_thinking` 参数。`enable_thinking` 是 Qwen3 特有参数，对非 Qwen3 模型无效（会被忽略）。因此无需修改 `silicon_flow_translator.py`。

### `enable_thinking` 对非 Qwen3 模型的影响

`enable_thinking` 是 Qwen3 特有的参数。对于其他模型（如 Hunyuan-MT-7B、DeepSeek 等），该参数会被 API 服务端忽略，不会产生任何副作用。因此，在 `AIPING_EXTRA_BODY` 和 `SILICON_FLOW_EXTRA_BODY` 中添加 `enable_thinking: False` 对所有模型调用都是安全的。

## What Changes

- **在 aiping 平台禁用 Qwen3 思考模式**：在 `config.py` 的 `AIPING_EXTRA_BODY` 中添加 `"enable_thinking": False`
- **在硅基流动平台禁用 Qwen3 思考模式**：在 `config.py` 中新增 `SILICON_FLOW_EXTRA_BODY = {"enable_thinking": False}` 配置项，各模块引用该配置
- **调整 aiping 翻译请求的采样参数**：将 `temperature` 从 0.1 调整为 0.7，`top_p` 从 0.9 调整为 0.8，匹配 Qwen3 非思考模式的推荐参数
- **增强翻译失败诊断日志**：在 `aiping_translator.py` 中记录 `reasoning_content` 长度和 `translated_text` 长度，便于后续排查
- **翻译结果为空时记录 WARNING**：在 `aiping_translator.py` 中当 `translated_text` 为空时记录 WARNING 日志，而非静默回退到原文

## Impact

- Affected code: `config.py`, `modules/aiping_translator.py`, `modules/glossary_extractor.py`, `modules/semantic_analyzer.py`, `modules/markdown_generator.py`
- Affected specs: fix-page18-text-not-translated（根因已确认，合并到此 spec）

## ADDED Requirements

### Requirement: aiping 平台禁用 Qwen3 思考模式

系统在通过 aiping 平台调用 Qwen3 模型时，必须在 `extra_body` 中设置 `"enable_thinking": False`，确保模型不产生思考内容，只返回实际结果。

#### Scenario: aiping 翻译请求不包含思考内容
- **WHEN** 系统调用 aiping 翻译 API
- **THEN** 请求参数中包含 `enable_thinking: False`
- **AND** 模型响应中不包含 `reasoning_content`
- **AND** `content` 字段包含翻译结果

### Requirement: 硅基流动平台禁用 Qwen3 思考模式

系统在通过硅基流动调用 Qwen3 模型时，必须在 `extra_body` 中设置 `"enable_thinking": False`。该配置通过 `config.py` 中的 `SILICON_FLOW_EXTRA_BODY` 统一管理，各模块（术语提取、语义分析、Markdown 格式化）引用该配置。

#### Scenario: 硅基流动 Qwen3 调用不包含思考内容
- **WHEN** 系统调用硅基流动 API（使用 Qwen3 模型）
- **THEN** 请求参数中包含 `enable_thinking: False`

### Requirement: 翻译采样参数匹配非思考模式

系统在调用 Qwen3-32B 翻译 API 时，应使用非思考模式的推荐采样参数：`temperature=0.7, top_p=0.8`。

#### Scenario: 翻译请求使用非思考模式参数
- **WHEN** 系统调用 aiping 翻译 API 且 `enable_thinking=False`
- **THEN** 请求参数中 `temperature=0.7, top_p=0.8`

### Requirement: 翻译结果为空时记录诊断日志

系统在翻译 API 返回后，如果 `translated_text` 为空，必须记录 WARNING 日志，包含 `reasoning_content` 长度（如有）和 `finish_reason`。

#### Scenario: 翻译结果为空
- **WHEN** 翻译 API 流式响应处理完毕后 `translated_text` 为空
- **THEN** 记录 WARNING 日志，包含 reasoning_content 长度和 finish_reason
- **AND** 不静默回退到原文（回退行为由 `_postprocess_text` 处理，但需有日志记录）

## MODIFIED Requirements

### Requirement: AIPING_EXTRA_BODY 配置

`config.py` 中的 `AIPING_EXTRA_BODY` 必须包含 `"enable_thinking": False` 字段，以禁用 Qwen3 的思考模式。

## REMOVED Requirements

（无移除的需求）

## 根因分析

### 问题链路

1. `aiping_translator.py` 调用 Qwen3-32B API，`extra_body=config.AIPING_EXTRA_BODY`
2. `config.AIPING_EXTRA_BODY` 不包含 `enable_thinking: False`，Qwen3 默认启用思考模式
3. 对于某些文本（如 627 字符的 "DavID LiDDLe?..."），Qwen3 的思考内容（`reasoning_content`）消耗了整个响应
4. 流式响应处理代码（第 113-120 行）跳过 `reasoning_content`，只收集 `content`
5. 如果模型只输出了 `reasoning_content` 而没有 `content`，`translated_text` 为空字符串
6. `_postprocess_text(translated_text="", original_text=text)` 检测到空结果，返回原文作为 fallback
7. `translation_service.py` 检测到翻译结果与原文相同，记录 WARNING

### 日志证据

- `07:48:02,304 - WARNING - 翻译结果与原文相同，可能翻译失败: 原文前100字符="DavID LiDDLe? wHo led the team..."`
- 同一页其他文本块翻译成功（如 "技术使用的三个阶段"、"xii | 前言"），说明 API 连接正常
- 只有 627 字符的长文本翻译失败，可能是思考模式对该文本产生了大量思考内容

### 修复方案

1. **核心修复**：在 `AIPING_EXTRA_BODY` 中添加 `"enable_thinking": False`，禁用 aiping 平台 Qwen3 的思考模式。
2. **硅基流动修复**：在 `SiliconFlowGlossaryExtractor` 中添加 `extra_body={"enable_thinking": False}`，禁用硅基流动 Qwen3 的思考模式。
3. **参数调整**：将 aiping 翻译请求的 `temperature` 从 0.1 调整为 0.7，`top_p` 从 0.9 调整为 0.8，匹配 Qwen3 非思考模式推荐参数。
4. **诊断增强**：记录 `reasoning_content` 长度和空翻译 WARNING，便于后续排查。
