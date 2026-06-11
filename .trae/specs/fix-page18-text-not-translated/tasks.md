# Tasks

- [x] Task 1: 在 config.py 中为 aiping 和硅基流动添加 EXTRA_BODY 配置
  - [x] SubTask 1.1: 在 `AIPING_EXTRA_BODY` 字典中添加 `"enable_thinking": False`
  - [x] SubTask 1.2: 在 `config.py` 中新增 `SILICON_FLOW_EXTRA_BODY = {"enable_thinking": False}` 配置项
- [x] Task 2: 在各模块中引用 SILICON_FLOW_EXTRA_BODY
  - [x] SubTask 2.1: 在 `modules/glossary_extractor.py` 的 `SiliconFlowGlossaryExtractor` 中使用 `config.SILICON_FLOW_EXTRA_BODY` 替代硬编码
  - [x] SubTask 2.2: 在 `modules/semantic_analyzer.py` 基类中使用 `config.SILICON_FLOW_EXTRA_BODY`
  - [x] SubTask 2.3: 在 `modules/markdown_generator.py` 基类 `MarkdownGenerator._call_api` 中使用 `config.SILICON_FLOW_EXTRA_BODY`
- [x] Task 3: 调整 aiping 翻译请求的采样参数匹配非思考模式
  - [x] SubTask 3.1: 在 `aiping_translator.py` 中将 `temperature` 从 0.1 调整为 0.7
  - [x] SubTask 3.2: 在 `aiping_translator.py` 中将 `top_p` 从 0.9 调整为 0.8
- [x] Task 4: 增强翻译失败诊断日志
  - [x] SubTask 4.1: 在 `aiping_translator.py` 流式响应处理中统计 `reasoning_content` 长度
  - [x] SubTask 4.2: 在流式响应处理完毕后，如果 `translated_text` 为空，记录 WARNING 日志（包含 reasoning_content 长度和 finish_reason）

# Task Dependencies

- Task 2 依赖 Task 1（需要先定义 SILICON_FLOW_EXTRA_BODY）
- Task 3 和 Task 4 独立于 Task 1 和 Task 2
