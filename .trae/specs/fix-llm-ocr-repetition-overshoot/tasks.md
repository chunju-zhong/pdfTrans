# Tasks

- [x] Task 1: 新增 LLM OCR 防重复参数配置项
  - [x] SubTask 1.1: 在 [config.py](file:///Users/chunju/work/pdfTrans/config.py) 第 151-154 行附近新增 `self.OCR_LLM_FREQUENCY_PENALTY = float(os.environ.get('OCR_LLM_FREQUENCY_PENALTY', '0.3'))`
  - [x] SubTask 1.2: 同位置新增 `self.OCR_LLM_PRESENCE_PENALTY = float(os.environ.get('OCR_LLM_PRESENCE_PENALTY', '0.2'))`
  - [x] SubTask 1.3: 在 [.env.example](file:///Users/chunju/work/pdfTrans/.env.example) OCR 相关配置块新增 `OCR_LLM_FREQUENCY_PENALTY`、`OCR_LLM_PRESENCE_PENALTY` 说明（注释默认值与作用）

- [x] Task 2: 修改 OCR_LLM_MAX_TOKENS 和 OCR_LLM_TEMPERATURE 默认值
  - [x] SubTask 2.1: 在 [config.py](file:///Users/chunju/work/pdfTrans/config.py:151) 将 `OCR_LLM_MAX_TOKENS` 默认值从 `'8000'` 改为 `'4096'`
  - [x] SubTask 2.2: 在 [config.py](file:///Users/chunju/work/pdfTrans/config.py:152) 将 `OCR_LLM_TEMPERATURE` 默认值从 `'0.1'` 改为 `'0.3'`
  - [x] SubTask 2.3: 在 [.env.example](file:///Users/chunju/work/pdfTrans/.env.example) 同步更新这两个变量的注释默认值

- [x] Task 3: 在 `chat.completions.create` 调用中传递防重复参数
  - [x] SubTask 3.1: 在 [modules/ocr/llm_extractor.py:383-388](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_extractor.py) 的 `chat.completions.create` 调用中新增 `frequency_penalty=config.OCR_LLM_FREQUENCY_PENALTY`
  - [x] SubTask 3.2: 同一调用新增 `presence_penalty=config.OCR_LLM_PRESENCE_PENALTY`
  - [x] SubTask 3.3: 确认参数对 DeepSeek-OCR 模型和通用 VLM 模型路径都生效（两路径共用同一 `create` 调用，已在第 383 行统一）

- [x] Task 4: 修正 `finish_reason=length` 日志建议方向
  - [x] SubTask 4.1: 在 [modules/ocr/llm_extractor.py:397-401](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_extractor.py) 将 `可考虑增大OCR_LLM_MAX_TOKENS` 改为 `请检查输出是否含重复短语，或调高 OCR_LLM_FREQUENCY_PENALTY`

- [x] Task 5: 更新 DeepSeek-OCR prompt，增加防重复指导
  - [x] SubTask 5.1: 在 [modules/ocr/llm_extractor.py:36](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_extractor.py) 的 `DEEPSEEK_OCR_PROMPT` 常量中追加防重复指导
  - [x] SubTask 5.2: 新 prompt 文本示例：`"<image>\n<|grounding|>Convert the document to markdown. Only transcribe text actually visible in the image. Do not repeat the same phrase. Output length must match the visible text amount."`

- [x] Task 6: 更新藏文 OCR 专项规则，增加防重复条目
  - [x] SubTask 6.1: 在 [prompts/language_rules/bo_to_zh.py:103-123](file:///Users/chunju/work/pdfTrans/prompts/language_rules/bo_to_zh.py) 的 OCR 规则 content 中新增条目
  - [x] SubTask 6.2: 新增条目内容：仅识别图像中实际可见的藏文字符；不要重复输出同一短语；输出长度应与图像实际文字量匹配

- [x] Task 7: 验证修复后的行为
  - [x] SubTask 7.1: 代码层面验证参数传递与日志输出符合预期（验证代理已确认所有代码检查点 PASS）
  - [ ] SubTask 7.2: 手动用 `app.log` 同样的输入（W3PD1098-v1.pdf 第 8-10 页，bo→zh，qianfan）重跑 OCR，确认：
    - 第 8 页 token 使用 completion 显著降低（目标 < 2000 tokens）
    - 第 8 页 OCR 输出不再含数十次重复同一短语
    - 第 10 页（原本正常）OCR 行为不受影响
    > 说明：需真实 Qianfan API 凭证与原 PDF，本次跳过实际行为复测，留待运行环境验证
  - [x] SubTask 7.3: 代码层面确认 DeepSeek-OCR prompt 修改仅为追加防重复指导，未删除原 markdown 转换指令，不影响非藏文文档 OCR

# Task Dependencies

- Task 1、Task 2 可并行（同文件不同行）
- Task 3 依赖 Task 1（需要 `OCR_LLM_FREQUENCY_PENALTY` 已定义）
- Task 4 独立
- Task 5 独立
- Task 6 独立
- Task 7 依赖 Task 1-6 全部完成
