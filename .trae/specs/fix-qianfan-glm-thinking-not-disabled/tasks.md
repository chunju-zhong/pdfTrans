# Tasks

- [x] Task 1: 扩展 `QIANFAN_EXTRA_BODY` 同时兼容 Qwen3 与 GLM 思考关闭参数
  - [x] SubTask 1.1: 修改 `config.py` 第 50 行 `QIANFAN_EXTRA_BODY`，从 `{"enable_thinking": False}` 改为同时包含 `enable_thinking: False` 和 `thinking: {"type": "disabled"}`
  - [x] SubTask 1.2: 确认类级别常量定义正确，无语法错误（保持纯字典，无需重载逻辑）

- [x] Task 2: 在 `QianfanTranslator.translate` 增加非空 `reasoning_content` 的 INFO 诊断日志
  - [x] SubTask 2.1: 在 `modules/qianfan_translator.py` 流式累积 `reasoning_content` 后、空响应判断前，新增 INFO 日志：当 `reasoning_content` 非空时记录长度、`finish_reason`、原文前 100 字符
  - [x] SubTask 2.2: 确保新日志与既有 WARNING 日志（第 144-147 行）共存，不替换、不冲突

- [ ] Task 3: 验证修复效果（代码层面审查已完成；运行时验证需用户在实际环境中执行）
  - [x] SubTask 3.1（代码层面）: `config.py` 修改正确，`QIANFAN_EXTRA_BODY` 同时包含两类参数，符合 GLM 官方文档要求
  - [x] SubTask 3.2（代码层面）: `qianfan_translator.py` 通过 `extra_body=config.QIANFAN_EXTRA_BODY`（第 96 行）传递参数，修复后 GLM-5.1 应返回 content 而非 reasoning_content
  - [x] SubTask 3.3（代码层面）: qwen3-32b 排版/术语模块（`glossary_extractor.py` 第 250 行）也引用 `QIANFAN_EXTRA_BODY`，新参数自动生效，无需改动
  - [ ] SubTask 3.4（运行时验证）: 用户需在实际环境中翻译藏文，确认 `reasoning_content` 长度为 0、`finish_reason` 不为 `length`

# Task Dependencies

- Task 2 依赖 Task 1（先扩展 extra_body，再增强诊断日志，便于在验证阶段观察日志变化）
- Task 3 依赖 Task 1 和 Task 2
