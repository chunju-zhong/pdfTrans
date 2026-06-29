# Tasks

- [ ] Task 1: 将 `QianfanTranslator.translate` 和 `SiliconFlowTranslator.translate` 改为流式调用，消除长文本读超时
  - [ ] SubTask 1.1: 在 [modules/qianfan_translator.py](file:///Users/chunju/work/pdfTrans/modules/qianfan_translator.py) 的 `translate` 方法中，将 `self.client.chat.completions.create(...)` 的 `stream=False` 改为 `stream=True`
  - [ ] SubTask 1.2: 移除 `result_text = response.choices[0].message.content or ""` 这行直接读取非流式响应的代码
  - [ ] SubTask 1.3: 新增流式响应收集循环：初始化 `result_text = ""`，遍历 `response` 中的 chunk，当 `chunk.choices` 非空且 `chunk.choices[0].delta.content` 存在时追加到 `result_text`
  - [ ] SubTask 1.4: 保持 `_postprocess_result(result_text)` 调用、`_is_translation_unchanged` 检测、`TranslationResult` 构造逻辑完全不变
  - [ ] SubTask 1.5: 确认 `api_kwargs`、`extra_body`、`messages` 在流式调用下仍被正确传递（参考 `modules/translator.py:191` 已修复的 `format_blocks` 流式实现）
  - [ ] SubTask 1.6: 在 [modules/silicon_flow_translator.py:86-103](file:///Users/chunju/work/pdfTrans/modules/silicon_flow_translator.py) 的 `translate` 方法中，将 `stream=False` 改为 `stream=True`
  - [ ] SubTask 1.7: 将 SiliconFlow 非流式响应处理代码（第 105-120 行 `choice.message.content` / `choice.message.reasoning_content` / `choice.finish_reason` 读取）替换为流式 chunk 收集循环：初始化 `translated_text = ""`、`reasoning_content = ""`、`finish_reason = ""`、`token_usage = {}`，遍历 chunk 累积 `delta.content` 到 `translated_text`、`delta.reasoning_content` 到 `reasoning_content`，从最后一个 chunk 的 `choices[0].finish_reason` 读取 `finish_reason`，从 `chunk.usage` 读取 `token_usage`
  - [ ] SubTask 1.8: 保留 SiliconFlow 现有的 `reasoning_content` fallback 逻辑（当 `translated_text` 为空时使用 `reasoning_content`）、`_postprocess_text` 调用、`TranslationResult` 构造完全不变
  - [ ] SubTask 1.9: 确认 SiliconFlow 的 `extra_body=config.SILICON_FLOW_EXTRA_BODY`、`temperature`、`top_p`、`max_tokens`、`messages` 在流式调用下仍被正确传递

- [ ] Task 2: 禁用 `QianfanTranslator` 和 `SiliconFlowTranslator` 客户端的 OpenAI SDK 自动重试
  - [ ] SubTask 2.1: 在 [modules/qianfan_translator.py](file:///Users/chunju/work/pdfTrans/modules/qianfan_translator.py) 第 26-30 行的 `OpenAI(...)` 构造中新增 `max_retries=0` 参数
  - [ ] SubTask 2.2: 确认 `timeout=config.TRANSLATION_TIMEOUT` 保持不变（流式已能解决超时，无需调大）
  - [ ] SubTask 2.3: 在 Qianfan except 分支（第 164-165 行）的异常消息中保留 "百度千帆翻译API请求失败:" 前缀，确保日志可识别
  - [ ] SubTask 2.4: 在 [modules/silicon_flow_translator.py:24-28](file:///Users/chunju/work/pdfTrans/modules/silicon_flow_translator.py) 的 `OpenAI(...)` 构造中新增 `max_retries=0` 参数
  - [ ] SubTask 2.5: 确认 SiliconFlow 的 `timeout=config.TRANSLATION_TIMEOUT` 保持不变
  - [ ] SubTask 2.6: 在 SiliconFlow except 分支（第 162-163 行）的异常消息中保留 "硅基流动翻译API请求失败:" 前缀，确保日志可识别

- [ ] Task 3: 在 `TextBlock` 模型上新增 `translation_failed` 字段
  - [ ] SubTask 3.1: 在 [models/text_block.py](file:///Users/chunju/work/pdfTrans/models/text_block.py) 的 `TextBlock` 类中新增字段 `translation_failed: bool = False`
  - [ ] SubTask 3.2: 确认 `copy()` 方法复制时保留 `translation_failed` 字段值
  - [ ] SubTask 3.3: 在 [models/merged_block.py](file:///Users/chunju/work/pdfTrans/models/merged_block.py) 的 `MergedBlock` 类中同样新增 `translation_failed: bool = False`（保持与 `TextBlock` 一致，便于下游统一判断）

- [ ] Task 4: 翻译失败时调用 `task.add_warning` 通知用户
  - [ ] SubTask 4.1: 在 [services/translation_content.py](file:///Users/chunju/work/pdfTrans/services/translation_content.py) 第 558-586 行的 `process_original_blocks` except 分支中，在 `logger.error` 之后调用 `task.add_warning(f"页面 {block.page_num} 块 {index+1} 翻译失败：{str(e)}；已回退到原文")`
  - [ ] SubTask 4.2: 在 `process_merged_blocks` 第 356-362 行的 except 分支中，同样调用 `task.add_warning`，消息形如 `f"合并块（页 {block.original_blocks[0].page_num if block.original_blocks else '?'}）翻译失败：{str(e)}；已回退到原文"`
  - [ ] SubTask 4.3: 确认 `task` 对象在两个方法的作用域内可访问（检查方法签名或闭包变量）

- [ ] Task 5: 在失败块上设置 `translation_failed=True` 标记
  - [ ] SubTask 5.1: 在 `process_original_blocks` 的 except 分支中，`fallback_text_block = block.copy()` 之后设置 `fallback_text_block.translation_failed = True`
  - [ ] SubTask 5.2: 同样在 `fallback_merged = MergedBlock(...)` 构造时传入 `translation_failed=True`，或构造后赋值
  - [ ] SubTask 5.3: 在 `process_merged_blocks` 的 except 分支中，对回退的 `b.copy()` 块设置 `translation_failed=True`

- [ ] Task 6: `format_blocks` 循环跳过 `translation_failed=True` 的块
  - [ ] SubTask 6.1: 在 [services/translation_content.py](file:///Users/chunju/work/pdfTrans/services/translation_content.py) 第 140-158 行的格式排版循环中，过滤掉 `tb.translation_failed=True` 的块
  - [ ] SubTask 6.2: 当某页所有块都失败时，跳过整页 `format_blocks` 调用（避免空列表请求 LLM）
  - [ ] SubTask 6.3: 当某页只有部分块失败时，仅对成功块调用 `format_blocks`，并按原索引位置写回（注意 `format_blocks` 返回列表与输入列表的索引对应关系——只传成功块时返回列表长度会减少，需要建立索引映射）
  - [ ] SubTask 6.4: 在日志中记录跳过的块，形如 `任务 {task_id} 页面 {page_num} 跳过 {n} 个翻译失败块的格式排版`

- [ ] Task 7: 验证修复后的行为
  - [ ] SubTask 7.1: 运行 `tests/test_qianfan_translator.py`（若存在）或相关翻译器测试，确认 Qianfan 流式响应拼装结果与非流式一致
  - [ ] SubTask 7.2: 运行 `tests/test_silicon_flow_translator.py`（若存在）或相关翻译器测试，确认 SiliconFlow 流式响应拼装结果与非流式一致，且 `reasoning_content` fallback 逻辑正常工作
  - [ ] SubTask 7.3: 运行 `tests/test_translation_content.py`（若存在）或相关翻译流程测试，确认失败块被正确标记和跳过
  - [ ] SubTask 7.4: 手动用 `app.log` 同样的输入（W3PT1098-v1.pdf 第 8-10 页，bo→zh，qianfan）重跑翻译，确认：
    - 第 8 页不再出现 `Request timed out`（流式不超时）
    - 即使仍超时，任务结果中出现 `add_warning` 提示
    - 日志中不再出现对失败块的 `格式排版 'ཁྲིད་...' -> 'ཁྲིད་...'` 行
    - 失败块的最终 `block_text` 仍是原文藏文（保留回退行为）
  - [ ] SubTask 7.5: 确认成功块（页 9、页 10）的翻译和排版行为不受影响
  - [ ] SubTask 7.6: 确认 SiliconFlow 翻译路径在流式改造后，对正常文本的翻译结果与非流式一致（reasoning_content fallback 路径不影响正常场景）

# Task Dependencies

- Task 3 依赖 Task 1、Task 2 完成后才能验证流式行为（但 Task 3 本身可独立实现，仅字段定义）
- Task 5 依赖 Task 3（需要 `translation_failed` 字段已定义）
- Task 6 依赖 Task 3 和 Task 5（需要失败块已被标记）
- Task 7 依赖 Task 1-6 全部完成
- Task 1 的 SubTask 1.1-1.5（Qianfan）和 SubTask 1.6-1.9（SiliconFlow）可并行
- Task 2 的 SubTask 2.1-2.3（Qianfan）和 SubTask 2.4-2.6（SiliconFlow）可并行
- Task 4 可与 Task 5 并行（不同方法分支）
