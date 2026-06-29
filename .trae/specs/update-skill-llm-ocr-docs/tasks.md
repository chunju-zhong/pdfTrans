# Tasks

- [x] Task 1: 更新 SKILL.md 中 OCR 参数说明
  - [x] 1.1: 更新 `--ocr-engine` 参数说明，标注支持 `paddleocr` 和 `llm` 两个选项
  - [x] 1.2: 更新 OCR 使用示例，添加 `--ocr-engine llm` 的示例

- [x] Task 2: 新增 LLM OCR 引擎功能说明章节
  - [x] 2.1: 在 OCR模式说明 下新增 LLM OCR 引擎小节，说明工作原理（通过 OpenAI 兼容 API 调用视觉模型）
  - [x] 2.2: 说明 LLM OCR 支持的模型（DeepSeek-OCR-2、Qwen3-VL 等）
  - [x] 2.3: 说明 LLM OCR 的两种响应格式（JSON 格式用于通用 VLM，Markdown/<|ref|> 格式用于 DeepSeek-OCR 原生格式）
  - [x] 2.4: 说明 LLM OCR 的功能（文本识别、表格识别、图表识别、公式识别）

- [x] Task 3: 新增 LLM OCR 环境变量配置说明
  - [x] 3.1: 在 API密钥配置 章节添加 LLM OCR 相关环境变量（AIPING_OCR_LLM_MODEL、SILICON_FLOW_OCR_LLM_MODEL、OCR_LLM_MAX_TOKENS、OCR_LLM_TEMPERATURE、OCR_LLM_DPI）

- [x] Task 4: 更新 OCR 注意事项
  - [x] 4.1: 添加 LLM OCR 特有的注意事项（API 调用费用、token 消耗、网络依赖等）

# Task Dependencies
- Task 2 依赖 Task 1（先更新参数说明，再添加详细功能说明）
- Task 3 和 Task 4 可与 Task 2 并行
