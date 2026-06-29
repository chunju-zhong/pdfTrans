# 修复千帆 GLM-5.1 思考模式未关闭 Spec

## Why

百度千帆平台已将翻译模型切换为 GLM-5.1（`.env` 中 `QIANFAN_MODEL_TRANSLATION=glm-5.1`），但日志显示 GLM-5.1 翻译藏文时输出了完整的思考过程（`reasoning_content` 长度=10164，`finish_reason=length`），实际翻译内容 `content` 为空，最终被代码 fallback 误当作翻译结果返回：

```
2026-06-28 22:02:11,850 - modules.qianfan_translator - WARNING - 百度千帆翻译结果为空: reasoning_content长度=10164, finish_reason=length, 原文前100字符='སྟོང་གཟུགས་ཨོ་རྒྱ་དྲུངས་ས་གསུམ་ཁྱབ།'
2026-06-28 22:02:11,851 - services.translation_content - INFO - 翻译结果: 结果前200字符="1.  **分析源文本**：`སྟོང་གཟུགས་ཨོ་རྒྱ་དྲུངས་ས་གསུམ་ཁྱབ།` \n2.  **逐词拆解与翻译**：..."
```

## 根因分析

### 参数不匹配（核心问题）

当前 `config.py` 第 50 行：
```python
QIANFAN_EXTRA_BODY = {"enable_thinking": False}
```

`enable_thinking` 是 **Qwen3 系列特有参数**（参考 `fix-page18-text-not-translated` spec 中的官方说明），对 GLM-5.1 **完全无效**，会被服务端忽略。

### GLM-5.1 官方思考参数

根据智谱 BigModel 官方文档（https://docs.bigmodel.cn/cn/guide/capabilities/thinking）：

- **GLM-5.2 / GLM-5.1 / GLM-5 / GLM-5-Turbo / GLM-5V-Turbo / GLM-4.6 / GLM-4.6V / GLM-4.5**：默认开启"动态思考"模式（模型自动判断是否思考）
- **关闭思考**：通过 `thinking: {"type": "disabled"}` 参数（顶层或 `extra_body`）
- **开启思考**：通过 `thinking: {"type": "enabled"}`
- **`reasoning_effort`**：仅 GLM-5.2 及以上支持，GLM-5.1 不支持此参数

### 千帆平台多模型并存

`.env` 中千帆平台同时使用两类模型：
- `QIANFAN_MODEL_TRANSLATION=glm-5.1`（GLM 系列）
- `QIANFAN_MODEL_LAYOUT=qwen3-32b`（Qwen3 系列）
- `QIANFAN_MODEL_GLOSSARY=qwen3-32b`（Qwen3 系列）

`QIANFAN_EXTRA_BODY` 同时被翻译、排版、术语提取模块引用，必须同时兼容两类模型。

### 影响：fallback 误用 reasoning_content

`modules/qianfan_translator.py` 第 141-149 行已有空响应 fallback 逻辑：当 `translated_text` 为空时，将 `reasoning_content` 作为翻译结果。本次问题中 GLM-5.1 的思考过程被错误地写入翻译结果，根因是思考模式未关闭，而非 fallback 逻辑本身有问题。修复需聚焦在"正确关闭思考"而非"移除 fallback"。

## What Changes

- **修改 `config.py` 第 50 行**：将 `QIANFAN_EXTRA_BODY` 从 `{"enable_thinking": False}` 扩展为同时包含两类参数：
  ```python
  QIANFAN_EXTRA_BODY = {
      "enable_thinking": False,            # Qwen3 系列关闭思考
      "thinking": {"type": "disabled"},    # GLM-4.5+/5.x 系列关闭思考
  }
  ```
  各模型服务端会忽略自身不识别的参数，互不冲突。
- **保持 `SILICON_FLOW_EXTRA_BODY` 不变**：硅基流动平台当前未使用 GLM 系列模型（翻译用 Hunyuan-MT-7B，排版/术语用 Qwen3-32B），暂不扩展。
- **保持 `AIPING_EXTRA_BODY` 不变**：aiping 是智能路由平台，平台层会按模型适配参数；且 aiping 平台未配置 GLM 模型。
- **增强诊断日志**：在 `qianfan_translator.py` 中，当 `reasoning_content` 非空时（无论 `content` 是否为空）记录 INFO 日志，便于后续监控"思考模式是否真正关闭"——若修复生效，`reasoning_content` 长度应恒为 0。

## Impact

- Affected specs:
  - `fix-page18-text-not-translated`（aiping/Qwen3 思考关闭，本次扩展至千帆 GLM）
  - `fix-siliconflow-qianfan-empty-response-handling`（千帆空响应 fallback，本次从源头消除空响应诱因）
- Affected code:
  - `config.py` — 修改 `QIANFAN_EXTRA_BODY` 第 50 行
  - `modules/qianfan_translator.py` — 增加非空 `reasoning_content` 的 INFO 诊断日志
- 不影响 `modules/silicon_flow_translator.py`、`modules/aiping_translator.py`
- 不影响 `modules/qianfan_semantic_analyzer.py`、`modules/qianfan_glossary_extractor.py`（它们引用 `QIANFAN_EXTRA_BODY`，新参数自动生效，无需改动）

## ADDED Requirements

### Requirement: 千帆 extra_body 同时兼容 Qwen3 与 GLM 思考关闭参数

系统 SHALL 在 `config.QIANFAN_EXTRA_BODY` 中同时包含 `enable_thinking: False`（适用于 Qwen3 系列）和 `thinking: {"type": "disabled"}`（适用于 GLM-4.5+/5.x 系列），使千帆平台的多模型调用（GLM-5.1 翻译、Qwen3-32B 排版/术语）都能正确关闭思考模式。

#### Scenario: GLM-5.1 翻译调用关闭思考
- **WHEN** 系统通过千帆平台调用 `glm-5.1` 模型翻译藏文
- **THEN** API 请求 `extra_body` 中包含 `thinking: {"type": "disabled"}`
- **AND** 模型响应中 `reasoning_content` 字段为空或不存在
- **AND** `content` 字段包含实际翻译结果
- **AND** `finish_reason` 不为 `length`（未被思考内容耗尽 max_tokens）

#### Scenario: Qwen3-32B 排版/术语调用关闭思考
- **WHEN** 系统通过千帆平台调用 `qwen3-32b` 模型进行排版或术语提取
- **THEN** API 请求 `extra_body` 中包含 `enable_thinking: False`
- **AND** 模型响应中 `reasoning_content` 字段为空或不存在

#### Scenario: 多模型参数互不冲突
- **WHEN** 千帆平台收到同时包含 `enable_thinking` 和 `thinking` 的请求
- **THEN** Qwen3 模型服务端 SHALL 忽略 `thinking` 参数
- **AND** GLM 模型服务端 SHALL 忽略 `enable_thinking` 参数
- **AND** 不返回参数错误（4xx）

### Requirement: 千帆翻译器记录 reasoning_content 诊断日志

系统 SHALL 在 `QianfanTranslator.translate` 中，当累积到的 `reasoning_content` 非空时记录 INFO 诊断日志，包含 `reasoning_content` 长度、`finish_reason`、原文前 100 字符，用于监控思考模式是否真正关闭。

#### Scenario: 修复生效后无 reasoning_content
- **WHEN** 修复部署后调用 GLM-5.1 翻译
- **THEN** 累积的 `reasoning_content` 长度应为 0
- **AND** 不记录 INFO 诊断日志（条件未满足）

#### Scenario: 异常情况下仍有 reasoning_content
- **WHEN** 因模型升级或参数变更导致 `reasoning_content` 非空
- **THEN** 记录 INFO 日志：`百度千帆翻译残留 reasoning_content: 长度=N, finish_reason=X, 原文前100字符='...'`
- **AND** 不影响原有 WARNING 日志和 fallback 逻辑

## MODIFIED Requirements

### Requirement: QIANFAN_EXTRA_BODY 配置

`config.py` 中的 `QIANFAN_EXTRA_BODY` SHALL 同时包含 `enable_thinking: False` 和 `thinking: {"type": "disabled"}` 两个字段，覆盖 Qwen3 与 GLM 两类模型的思考关闭参数。

## REMOVED Requirements

（无移除的需求）
