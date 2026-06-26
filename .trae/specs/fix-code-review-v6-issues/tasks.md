# Tasks
- [x] Task 1: OCR_LLM_TIMEOUT 接入客户端 + 超时消息动态化（Issues 1+4）
  - [x] SubTask 1.1: 将 `llm_extractor.py` 中 OpenAI 客户端 `timeout` 参数从 `120.0` 改为 `config.OCR_LLM_TIMEOUT`
  - [x] SubTask 1.2: 将 `timeout_error_msg` 中的 `120秒` 改为 `{config.OCR_LLM_TIMEOUT}秒`
  - [x] SubTask 1.3: 移除 `except APITimeoutError as e:` 中未使用的 `e`（Issue 5）

- [x] Task 2: 删除 `OCR_LLM_EXTRA_BODY` 死配置（Issue 2）
  - [x] SubTask 2.1: 从 `config.py` 中删除 `OCR_LLM_EXTRA_BODY` 定义

- [x] Task 3: 提取通用超时错误处理方法消除重复（Issue 3）
  - [x] SubTask 3.1: 在 `translation_service.py` 中添加 `_handle_ocr_timeout_errors` 静态方法，封装超时检查逻辑
  - [x] SubTask 3.2: 替换 3 处重复逻辑为调用该方法

# Task Dependencies
- 无依赖关系，Tasks 1~3 可并行执行
