# 诊断 GLM-4.6V 翻译藏文页面持续重试 Spec

## Why
使用 `AIPING_OCR_LLM_MODEL=GLM-4.6V` 翻译第6页藏文时，请求一直重试无法完成。日志显示 OpenAI SDK 内置重试机制反复触发，需要定位根因并修复。

## 根因分析

### 时间线还原
```
23:38:53 - LLM OCR提取第6/728页（开始请求）
23:40:55 - Retrying request to /chat/completions in 0.386528s（第1次重试，距开始约122秒）
23:42:56 - Retrying request to /chat/completions in 0.757839s（第2次重试，距上次约121秒）
```

### 根因：GLM-4.6V 响应超时 + OpenAI SDK 默认重试

1. **超时阈值过低**：`llm_extractor.py` 第184行设置 `timeout=120.0`（120秒），GLM-4.6V 处理藏文页面（低资源语言+复杂文字）响应时间超过120秒，触发 `ReadTimeout` 异常。

2. **OpenAI SDK 默认重试2次**：`OpenAI()` 客户端默认 `max_retries=2`，SDK 对连接错误和超时自动重试。每次重试又超时120秒，导致总耗时约 120×3=360秒（6分钟）才最终失败。

3. **重试无意义**：GLM-4.6V 对藏文页面的处理时间稳定超过120秒，简单重试只会重复超时，不会成功。

4. **额外问题**：`OCR_LLM_EXTRA_BODY` 中的 `provider.sort: "output_price"` 配置导致 aiping 路由到响应慢的供应商，加剧超时。实测纯文本请求 `output_price` 比 `latency` 慢 4x（6.1s vs 1.4s），藏文图像 OCR 时差距更大。

### 次要因素
- GLM-4.6V 不是 DeepSeek-OCR 模型，走的是通用 VLM JSON prompt 路径，prompt 更长，token 消耗更大
- 藏文 prompt 中包含 `LOW_RESOURCE_LANGS` 的额外提示文本，进一步增加了输入 token

## What Changes
- 增大 LLM OCR 的 OpenAI 客户端 timeout，从 120s 提升到 300s
- 将 OpenAI 客户端的 `max_retries` 设为 0，避免无意义的自动重试（应用层已有自己的重试逻辑）
- 增加 LLM OCR 超时相关的日志，记录请求耗时和超时原因
- 新增 `OCR_LLM_TIMEOUT` 环境变量配置，允许用户自定义超时时间
- 将 `OCR_LLM_EXTRA_BODY` 中 `provider.sort` 从 `output_price` 改为 `latency`，优先路由到低延迟供应商

## Impact
- Affected code:
  - `modules/ocr/llm_extractor.py` — OpenAI 客户端初始化、超时配置
  - `config.py` — 新增 `OCR_LLM_TIMEOUT` 配置项
  - `.env.example` — 新增环境变量说明

## ADDED Requirements

### Requirement: LLM OCR 超时可配置
系统 SHALL 支持通过 `OCR_LLM_TIMEOUT` 环境变量配置 LLM OCR 请求超时时间，默认 300 秒。

#### Scenario: 用户配置自定义超时
- **WHEN** 用户设置 `OCR_LLM_TIMEOUT=600`
- **THEN** LLM OCR 客户端使用 600 秒超时

#### Scenario: 用户未配置超时
- **WHEN** 用户未设置 `OCR_LLM_TIMEOUT`
- **THEN** LLM OCR 客户端使用默认 300 秒超时

### Requirement: 禁用 OpenAI SDK 自动重试
LLM OCR 的 OpenAI 客户端 SHALL 设置 `max_retries=0`，避免 SDK 层面的无意义超时重试。

#### Scenario: 请求超时
- **WHEN** LLM OCR 请求超时
- **THEN** 立即抛出超时异常，不进行 SDK 层面重试
- **AND** 应用层捕获异常并记录日志，返回 None（空页面）

### Requirement: LLM OCR 超时日志增强
当 LLM OCR 请求超时或失败时，SHALL 记录详细的错误信息，包括请求耗时、模型名称、页码。

#### Scenario: 超时日志
- **WHEN** LLM OCR 请求超时
- **THEN** 日志记录 "LLM OCR第N页请求超时(M秒)，模型: XXX"
