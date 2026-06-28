# Checklist

## 根因验证

- [ ] 已通过 `app.log` 第 60、106、120-122、124-125、151-167 行确认：第 8 页块 1 翻译超时后回退到原文藏文，最终 PDF 渲染的是原文藏文而非中文译文
- [ ] 已确认根因 1：`modules/qianfan_translator.py:90` 的 `stream=False` 导致 6319 字符藏文超过 30s 读超时
- [ ] 已确认根因 1b：`modules/silicon_flow_translator.py:88` 同样使用 `stream=False`，存在相同根因（用户要求一并修复）
- [ ] 已确认根因 2：`services/translation_content.py:571-586` 的 except 分支仅 `logger.error` 不调用 `task.add_warning`，用户无感知
- [ ] 已确认根因 3：`services/translation_content.py:140-158` 的 `format_blocks` 循环对失败块的原文藏文做无意义 LLM 排版，浪费调用且误导日志
- [ ] 已确认现有 spec `fix-format-blocks-timeout-retry` 在 `spec.md:24` 明确排除了 Qianfan translate 方法，本次修复补齐该遗漏（同时覆盖 SiliconFlow）

## 代码实现

- [ ] `QianfanTranslator.translate` 已改为 `stream=True`，并通过遍历 chunk 累积 `delta.content` 拼装响应
- [ ] `SiliconFlowTranslator.translate` 已改为 `stream=True`，并通过遍历 chunk 累积 `delta.content` 拼装响应
- [ ] SiliconFlow 流式响应保留了 `reasoning_content` fallback 逻辑（当 `delta.content` 为空时使用累积的 `reasoning_content`）
- [ ] SiliconFlow 流式响应正确读取 `finish_reason`（来自最后一个 chunk）和 `token_usage`（来自 `chunk.usage`）
- [ ] `QianfanTranslator` 的 `OpenAI(...)` 构造已显式设置 `max_retries=0`
- [ ] `SiliconFlowTranslator` 的 `OpenAI(...)` 构造已显式设置 `max_retries=0`
- [ ] `TextBlock` 模型已新增 `translation_failed: bool = False` 字段，`copy()` 保留该字段
- [ ] `MergedBlock` 模型已新增 `translation_failed: bool = False` 字段
- [ ] `process_original_blocks` 的 except 分支已调用 `task.add_warning` 通知用户
- [ ] `process_merged_blocks` 的 except 分支已调用 `task.add_warning` 通知用户
- [ ] `process_original_blocks` 的 except 分支已设置 `fallback_text_block.translation_failed = True`
- [ ] `process_merged_blocks` 的 except 分支已设置回退块 `translation_failed = True`
- [ ] `translate_content` 的格式排版循环已过滤 `translation_failed=True` 的块
- [ ] 部分块失败的页面，仅对成功块调用 `format_blocks` 并正确建立索引映射写回
- [ ] 整页失败时跳过 `format_blocks` 调用（避免空列表请求 LLM）

## 行为验证

- [ ] 长文本（>5000 字符）藏文翻译不再因读超时失败（Qianfan 路径）
- [ ] 长文本（>5000 字符）藏文翻译不再因读超时失败（SiliconFlow 路径）
- [ ] 即使翻译仍超时，任务结果中出现 `add_warning` 提示，用户可感知
- [ ] 失败块的 `block_text` 保持为原文藏文（保留回退行为，不破坏现有兜底）
- [ ] 失败块不再被 `format_blocks` 处理，日志中不再出现 `格式排版 'ཁྲིད་...' -> 'ཁྲིད་...'` 的误导行
- [ ] 成功块（页 9、页 10）的翻译和排版行为不受影响
- [ ] SiliconFlow 的 `reasoning_content` fallback 路径在流式改造后仍正常工作（翻译结果为空时使用 reasoning_content）

## 非目标确认

- [ ] 未修改 `config.TRANSLATION_TIMEOUT`（保持 30s，流式已能解决超时）
- [ ] 未对长文本输入做预分块（流式已能解决超时，分块会引入语义断裂风险，超出本次范围）
- [ ] 未修改 `AipingTranslator`（已使用 `stream=True`，无此问题）
