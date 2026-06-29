# 修复 format_blocks 排版重试超时问题 Spec

## Why

最新代码在翻译完成后进行 LLM 格式排版（`format_blocks`）时，几乎每次都会触发 OpenAI 客户端的重试（`Retrying request to /chat/completions`），每次重试间隔正好 30 秒，对应 `TRANSLATION_TIMEOUT=30`。日志证据：

```
22:32:34 - 任务 ... 页面 13 块 4: 格式排版 '目录  |  xi...' -> '...'
22:32:38 - HTTP Request: POST https://aiping.cn/api/v1/chat/completions "HTTP/1.1 200 OK"
22:33:08 - openai._base_client - INFO - Retrying request to /chat/completions in 0.442081 seconds
22:33:39 - openai._base_client - INFO - Retrying request to /chat/completions in 0.874065 seconds
```

200 OK 之后 30 秒整触发重试，是典型的 **读超时（read timeout）**：服务器返回响应头很快，但 `stream=False` 必须等待完整响应体；当一页文本块较多或 `max_tokens=4096` 较大时，LLM 生成完整响应的时间超过 30 秒，触发超时；OpenAI 客户端默认重试 2 次，但每次重试仍用同一个 30 秒超时，因此必然再次超时，最终要么抛异常要么浪费 90+ 秒。

翻译主流程（`translate`）使用 `stream=True`，token 增量到达会持续重置读定时器，所以不会触发该问题；只有 `format_blocks` 使用 `stream=False` 才暴露此缺陷。

## What Changes

- 将 `Translator.format_blocks` 的 LLM 调用从 `stream=False` 改为 `stream=True`，与翻译主流程保持一致，从根本上消除读超时。
- 为 `format_blocks` 的流式响应实现增量收集逻辑（累积 `delta.content`）。
- 保留现有的 `_parse_format_result` 解析逻辑与计数校验回退机制不变。
- 不修改 `TRANSLATION_TIMEOUT` 全局值（翻译主流程仍依赖它且工作正常）。
- 不修改 `qianfan_translator` / `silicon_flow_translator` 中各自的 `translate` 方法（它们已正确处理非流式响应，且不属于本次问题范围）。

## Impact

- Affected specs: 无直接相关 spec；本次为独立 bug 修复。
- Affected code:
  - [modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py) — `format_blocks` 方法（基类，所有翻译子类共享）
  - [modules/aiping_translator.py](file:///Users/chunju/work/pdfTrans/modules/aiping_translator.py) — 继承基类 `format_blocks`，无需改动
  - [modules/qianfan_translator.py](file:///Users/chunju/work/pdfTrans/modules/qianfan_translator.py) — 同上
  - [modules/silicon_flow_translator.py](file:///Users/chunju/work/pdfTrans/modules/silicon_flow_translator.py) — 同上
- 不影响翻译主流程、OCR、PDF 生成等其他模块。
- 不改变排版结果的格式与解析逻辑，仅改变传输方式。

## ADDED Requirements

### Requirement: format_blocks 使用流式调用

`Translator.format_blocks` 在调用 LLM 时 SHALL 使用 `stream=True`，并通过累积 `delta.content` 的方式组装最终响应文本，以避免非流式调用因 LLM 生成时间超过客户端读超时而触发无意义的重试。

#### Scenario: 大页面排版成功完成
- **WHEN** 某页包含较多文本块（例如 >10 个块或译文总长 >2000 字符），LLM 完整生成时间超过 30 秒
- **THEN** `format_blocks` 通过流式增量接收 token，持续重置读定时器，在无需重试的情况下成功完成排版
- **AND** 日志中不再出现 `Retrying request to /chat/completions` 由 `format_blocks` 触发的记录

#### Scenario: 流式响应正常解析
- **WHEN** LLM 流式返回包含 `---块N---` 标记的完整排版结果
- **THEN** `format_blocks` 累积所有 chunk 的 `delta.content` 后，调用 `_parse_format_result` 解析
- **AND** 解析结果与原 `stream=False` 实现完全一致（块数量校验、回退逻辑不变）

#### Scenario: 流式调用异常仍回退原文
- **WHEN** 流式调用过程中发生异常（网络错误、API 错误等）
- **THEN** `format_blocks` 捕获异常并记录 warning 日志，返回原始 `translated_texts`（与现有异常处理行为一致）

## MODIFIED Requirements

### Requirement: format_blocks 方法实现

`Translator.format_blocks`（[modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py)）的 LLM 调用部分修改如下：

1. 将 `self.client.chat.completions.create(...)` 调用中的 `stream=False` 改为 `stream=True`。
2. 移除直接读取 `response.choices[0].message.content` 的写法。
3. 新增流式响应收集循环：遍历响应 chunk，累积 `chunk.choices[0].delta.content` 到 `result_text`。
4. 循环结束后，将累积的 `result_text` 传给现有的 `self._parse_format_result(result_text, len(translated_texts))`。
5. 其余逻辑（计数校验、回退、异常处理）保持不变。

修改后的方法 SHALL 保持相同的函数签名、返回值结构与错误处理语义，确保对所有子类（AipingTranslator / QianfanTranslator / SiliconFlowTranslator）透明。

## REMOVED Requirements

无删除项。`_parse_format_result`、`_get_format_api_kwargs` 及子类钩子保持原样。
