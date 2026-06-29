# Tasks

- [x] Task 1: 新增 `OCR_LLM_TIMEOUT` 配置项
  - [x] 在 `config.py` 中新增 `OCR_LLM_TIMEOUT`，从环境变量读取，默认 300
  - [x] 在 `.env.example` 中新增 `OCR_LLM_TIMEOUT` 说明
- [x] Task 2: 修改 LlmOcrExtractor 客户端初始化
  - [x] 将 `timeout=120.0` 改为 `timeout=config.OCR_LLM_TIMEOUT`
  - [x] 添加 `max_retries=0` 禁用 SDK 自动重试
  - [x] 同时修改 aiping 和 silicon_flow 两个客户端初始化
- [x] Task 3: 增强超时日志
  - [x] 在 `_extract_page` 的 except 块中，区分超时异常和其他异常
  - [x] 超时时记录请求耗时、模型名称、页码等详细信息

# Task Dependencies
- Task 2 depends on Task 1（需要 config.OCR_LLM_TIMEOUT）
- Task 3 is independent
