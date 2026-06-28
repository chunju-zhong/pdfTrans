# Tasks

- [x] Task 1: 将 `Translator.format_blocks` 改为流式调用，消除排版读超时重试
  - [x] SubTask 1.1: 在 [modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py) 的 `format_blocks` 方法中，将 `self.client.chat.completions.create(...)` 的 `stream=False` 改为 `stream=True`
  - [x] SubTask 1.2: 移除 `result_text = response.choices[0].message.content or ""` 这行直接读取非流式响应的代码
  - [x] SubTask 1.3: 新增流式响应收集循环：初始化 `result_text = ""`，遍历 `response` 中的 chunk，当 `chunk.choices` 非空且 `chunk.choices[0].delta.content` 存在时追加到 `result_text`
  - [x] SubTask 1.4: 保持 `_parse_format_result(result_text, len(translated_texts))` 调用、计数校验、回退到 `translated_texts` 的异常处理逻辑完全不变
  - [x] SubTask 1.5: 确认 `api_kwargs = self._get_format_api_kwargs()` 与 `extra_body` 在流式调用下仍被正确传递（OpenAI SDK 流式与非流式均接受 `**api_kwargs`）

- [x] Task 2: 验证修复后的行为
  - [x] SubTask 2.1: 运行 `tests/test_translator.py` 中与 `format_blocks` 相关的测试，确认全部通过
  - [x] SubTask 2.2: 检查 `test_translator.py` 中是否存在 mock `stream=False` 的断言；若存在，需同步更新为 `stream=True`，确保测试与实现一致
  - [x] SubTask 2.3: 确认 `_parse_format_result` 对流式累积后的完整文本解析结果与非流式一致（块数量校验、`---块N---` 标记分割、回退逻辑）

# Task Dependencies
- Task 2 依赖 Task 1 完成后才能验证
