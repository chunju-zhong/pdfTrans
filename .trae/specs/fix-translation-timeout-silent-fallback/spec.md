# 修复翻译超时静默回退原文 Spec

## Why

使用 Qianfan 翻译藏文 PDF 第 8 页时（原文 6319 字符），翻译请求因 30s 读超时失败，但系统静默回退到原文藏文输出，用户在最终 PDF 中看到的是原文而非译文，且任务结果中没有任何翻译失败的提示。日志中仅有一行 `翻译原始块时出错: 百度千帆翻译API请求失败: Request timed out.`，但 `format_blocks` 仍对原文藏文执行了一次 LLM 调用，并在日志中输出 `页面 8 块 1: 格式排版 'ཁྲིད་...' -> 'ཁྲིད་...'`，造成"翻译成功"的假象。

## 根因分析

### 时间线还原（来自 app.log）

```
16:06:55,686 - 翻译请求: 原文前100字符="ཁྲིད་སངས་རྒྱས..." 长度=6319
16:07:25,772 - Retrying request to /chat/completions in 0.397388s   # SDK 第 1 次重试（30s 超时）
16:07:56,214 - Retrying request to /chat/completions in 0.856384s   # SDK 第 2 次重试（再 30s 超时）
16:08:27,130 - 翻译原始块时出错: 百度千帆翻译API请求失败: Request timed out.  # 最终失败，~91s
16:09:25,824 - 页面 8 块 1: 格式排版 'ཁྲིད་...' -> 'ཁྲིད་...'  # 对原文藏文做无意义的 LLM 排版
16:10:01,581 - 翻译文本: 'ཁྲིད་སངས་རྒྱས...' (共 977 字符)  # 最终 PDF 渲染的是原文藏文
```

### 根因 1：Qianfan 和 SiliconFlow 的 `translate` 都使用 `stream=False`，长文本必超时

- 文件：`modules/qianfan_translator.py:90`、`modules/silicon_flow_translator.py:88`
- 两者的 `chat.completions.create(..., stream=False)` 都必须等待完整响应体才返回
- 6319 字符藏文（低资源语言，token 化效率低，生成慢）超过 `config.TRANSLATION_TIMEOUT=30s` 读超时
- 两者 OpenAI SDK 均使用默认 `max_retries=2`，每次重试仍用同一 30s 超时，必然再次超时，浪费 ~90s
- 对比：`AipingTranslator.translate`（`modules/aiping_translator.py:94`）使用 `stream=True`，token 增量持续重置读定时器，不会触发此问题
- 对比：`Translator.format_blocks`（`modules/translator.py:191`）已被 `fix-format-blocks-timeout-retry` spec 修复为 `stream=True`，但该 spec 在 `spec.md:24` 明确写道"不修改 qianfan_translator / silicon_flow_translator 中各自的 translate 方法（它们已正确处理非流式响应，且不属于本次问题范围）"——此判断在 6319 字符藏文场景下被证伪

### 根因 2：异常处理静默回退到原文，无任何用户告警

- 文件：`services/translation_content.py:558-586`（`process_original_blocks` 的 except 分支）
- 异常被 `logger.error` 记录后未重新抛出，未调用 `task.add_warning`
- `MergedBlock.block_text = block.block_text`（第 580 行）和 `fallback_text_block = block.copy()`（第 585 行）直接保留原文藏文
- 块上没有 "translation_failed" 标记
- 用户在最终 PDF 上看到原文藏文，任务结果显示成功，完全无法感知翻译失败
- 对比：同一文件第 233/487 行的截断处理会调用 `task.add_warning`，超时分支却不会——不一致

### 根因 3：对未翻译的原文跑 `format_blocks`，浪费 LLM 调用且误导日志

- 文件：`services/translation_content.py:140-158`（`translate_content` 的格式排版步骤）
- 第 147 行 `[tb.block_text for tb in page_blocks.text_blocks]` 直接读取每个块的 `block_text`
- 失败块的 `block_text` 是原文藏文，被传入 `translator.format_blocks(translated_texts, target_lang)`
- `format_blocks` 只做标点/空白规范，不做翻译，输出仍是藏文
- 第 156 行写回 `block_text = formatted_text`，日志显示 `格式排版 'ཁྲིད་...' -> 'ཁྲིད་...'`，伪装成"翻译成功"
- 浪费一次 LLM 调用（且该调用本身也可能超时）

## What Changes

- 将 `QianfanTranslator.translate` 和 `SiliconFlowTranslator.translate` 都改为流式调用（`stream=True`），消除长文本读超时
- 在 `QianfanTranslator` 和 `SiliconFlowTranslator` 的 OpenAI 客户端构造中显式设置 `max_retries=0`，避免 SDK 层无意义重试浪费 60s
- 在 `services/translation_content.py` 的两个 except 分支（`process_original_blocks` 第 571 行、`process_merged_blocks` 第 356 行）调用 `task.add_warning`，明确告知用户翻译失败并已回退原文
- 在失败块上添加 `translation_failed` 标记字段，避免 `format_blocks` 对原文跑无意义的 LLM 排版
- 在 `translate_content` 的格式排版循环（第 140-158 行）跳过带 `translation_failed` 标记的块

## Impact

- Affected specs:
  - `fix-format-blocks-timeout-retry` — 该 spec 明确排除了 Qianfan translate，本 spec 补齐该遗漏（同时覆盖 SiliconFlow）
  - `add-translation-truncation-fallback` — 渲染层截断兜底，与本 spec 请求层超时修复正交
  - `fix-short-text-untranslated-detection` — 检测 LLM 返回原文，与本 spec 的翻译失败回退正交
- Affected code:
  - `modules/qianfan_translator.py` — `translate` 方法改流式、客户端加 `max_retries=0`
  - `modules/silicon_flow_translator.py` — `translate` 方法改流式、客户端加 `max_retries=0`（根因与 Qianfan 一致：第 88 行 `stream=False`，第 24-28 行 OpenAI 客户端未设置 `max_retries`，SDK 默认 `max_retries=2` 同样会浪费 60s）
  - `services/translation_content.py` — 两个 except 分支加 `task.add_warning`、失败块加标记、`format_blocks` 循环跳过失败块
  - `models/text_block.py` 或 `models/merged_block.py` — `TextBlock` 新增 `translation_failed: bool` 字段（默认 False）

## ADDED Requirements

### Requirement: Qianfan 和 SiliconFlow 翻译主流程使用流式响应

`QianfanTranslator.translate` 和 `SiliconFlowTranslator.translate` SHALL 使用 `stream=True` 调用 `chat.completions.create`，并通过遍历 chunk 累积 `delta.content` 拼装完整响应。两者根因一致（均使用 `stream=False`），修复方式一致。

#### Scenario: 长文本翻译不超时
- **WHEN** 输入文本长度超过 5000 字符（如 6319 字符藏文）
- **AND** 模型生成完整响应需要 60s
- **THEN** 由于流式 token 增量持续重置读定时器，请求不触发 `Request timed out`
- **AND** 翻译结果正常返回

#### Scenario: 流式响应拼装完整
- **WHEN** 流式响应包含多个 chunk
- **THEN** 遍历 `response` 中所有 chunk
- **AND** 当 `chunk.choices` 非空且 `chunk.choices[0].delta.content` 存在时追加到 `result_text`
- **AND** 最终 `result_text` 与非流式响应的 `response.choices[0].message.content` 内容一致

#### Scenario: SiliconFlow 流式响应保留 reasoning_content fallback
- **WHEN** `SiliconFlowTranslator.translate` 流式调用时 `delta.content` 累积为空
- **AND** 某些 chunk 的 `delta.reasoning_content` 非空
- **THEN** 累积 `delta.reasoning_content` 作为 fallback
- **AND** 当 `delta.content` 为空时使用累积的 `reasoning_content` 作为翻译结果
- **AND** `finish_reason` 和 `token_usage` 从最后一个 chunk 的 `choices[0].finish_reason` 和 `chunk.usage` 读取

### Requirement: 禁用 OpenAI SDK 自动重试

`QianfanTranslator` 和 `SiliconFlowTranslator` 的 OpenAI 客户端 SHALL 设置 `max_retries=0`，避免 SDK 层面的无意义超时重试。两者客户端构造（`modules/qianfan_translator.py` 和 `modules/silicon_flow_translator.py:24-28`）当前均依赖 SDK 默认 `max_retries=2`，长文本超时场景下会浪费约 60s。

#### Scenario: 请求超时
- **WHEN** 流式请求仍因网络/服务异常超时
- **THEN** 立即抛出超时异常，不进行 SDK 层面重试
- **AND** 异常被 `services/translation_content.py` 的 except 分支捕获并处理

### Requirement: 翻译失败时通知用户

当单个文本块翻译失败并回退到原文时，系统 SHALL 通过 `task.add_warning` 向用户发送明确告警，告知哪一页哪个块翻译失败、失败原因、已回退原文。

#### Scenario: 翻译超时回退原文
- **WHEN** `process_original_blocks` 中某块 `future.result()` 抛出 `百度千帆翻译API请求失败: Request timed out.` 或 `硅基流动翻译API请求失败: Request timed out.`
- **THEN** 调用 `task.add_warning(f"页面 {page_num} 块 {index+1} 翻译失败：{str(e)}；已回退到原文")`
- **AND** 任务结果中包含该告警
- **AND** 用户在前端能看到翻译失败提示

#### Scenario: 合并块翻译超时回退原文
- **WHEN** `process_merged_blocks` 中某块翻译失败
- **THEN** 同样调用 `task.add_warning`，告知合并块翻译失败并已回退原文

### Requirement: 翻译失败块跳过格式排版

`TextBlock` SHALL 新增 `translation_failed: bool` 字段（默认 False）。当块翻译失败回退到原文时，该字段被设为 True。`translate_content` 的格式排版循环 SHALL 跳过 `translation_failed=True` 的块，不对原文执行无意义的 LLM 排版。

#### Scenario: 失败块跳过 format_blocks
- **WHEN** `format_blocks` 循环遍历页面块的 `block_text`
- **AND** 某块的 `translation_failed=True`
- **THEN** 跳过该块，不将其 `block_text` 加入 `translated_texts` 列表
- **AND** 不对该块调用 `translator.format_blocks`
- **AND** 该块的 `block_text` 保持为原文藏文

#### Scenario: 成功块仍正常排版
- **WHEN** 块的 `translation_failed=False`
- **THEN** 正常加入 `translated_texts` 列表，调用 `format_blocks` 排版

## MODIFIED Requirements

### Requirement: 翻译块失败处理

`process_original_blocks` 和 `process_merged_blocks` 的 except 分支在捕获翻译异常时，SHALL：

1. 调用 `task.add_warning` 通知用户（新增）
2. 在回退的 `TextBlock` 上设置 `translation_failed=True`（新增）
3. 保留 `block_text=block.block_text` 回退原文行为（不变）
4. 保留 `logger.error` 记录日志（不变）

## REMOVED Requirements

（无）
