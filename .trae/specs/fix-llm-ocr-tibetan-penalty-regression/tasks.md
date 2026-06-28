# Tasks

- [x] Task 1: 恢复 `config.py` 中 LLM OCR 参数默认值
  - [x] SubTask 1.1: 将 `OCR_LLM_FREQUENCY_PENALTY` 默认值从 `0.3` 改为 `0.0`
  - [x] SubTask 1.2: 将 `OCR_LLM_PRESENCE_PENALTY` 默认值从 `0.2` 改为 `0.0`
  - [x] SubTask 1.3: 将 `OCR_LLM_TEMPERATURE` 默认值从 `0.3` 恢复为 `0.1`
  - [x] SubTask 1.4: 将 `OCR_LLM_MAX_TOKENS` 默认值从 `4096` 恢复为 `8000`

- [x] Task 2: 简化 `modules/ocr/llm_extractor.py` 中的 `DEEPSEEK_OCR_PROMPT` 并为 DeepSeek-OCR 模式注入 `lang_hint`
  - [x] SubTask 2.1: 将 `DEEPSEEK_OCR_PROMPT` 恢复为 `"<image>\n<|grounding|>Convert the document to markdown."`，移除被模型回显的三句英文短语
  - [x] SubTask 2.2: 将 VLM 分支中的 `lang_hint` 加载逻辑提取为私有方法 `_build_lang_hint(self) -> str`，根据 `self.source_lang` 从 `prompts.rule_registry` 加载 `task_type="ocr"` 的规则内容并用 `\n` 连接
  - [x] SubTask 2.3: 在 DeepSeek-OCR 分支调用 `_build_lang_hint()`，将结果追加到 user 消息文本末尾（`DEEPSEEK_OCR_PROMPT + lang_hint`）
  - [x] SubTask 2.4: 在 VLM 分支调用 `_build_lang_hint()` 替换原有的内联加载逻辑，保持行为一致
  - [x] SubTask 2.5: 确保 `ImportError` 时 `lang_hint` 为空字符串（向后兼容）

- [x] Task 3: 更新 `.env.example` 中 OCR LLM 参数注释
  - [x] SubTask 3.1: 更新 `OCR_LLM_MAX_TOKENS` 注释为 `8000`
  - [x] SubTask 3.2: 更新 `OCR_LLM_TEMPERATURE` 注释为 `0.1`
  - [x] SubTask 3.3: 更新 `OCR_LLM_FREQUENCY_PENALTY` 注释为 `0.0` 并附说明"OCR 转录任务不应使用频率惩罚"
  - [x] SubTask 3.4: 更新 `OCR_LLM_PRESENCE_PENALTY` 注释为 `0.0` 并附说明"OCR 转录任务不应使用存在惩罚"

- [x] Task 4: 移除 `prompts/language_rules/bo_to_zh.py` 中藏文 OCR 规则的防重复条目
  - [x] SubTask 4.1: 删除原第 6 条（"仅识别图像中实际可见的藏文字符..."）
  - [x] SubTask 4.2: 删除原第 7 条（"不要重复输出同一短语..."）
  - [x] SubTask 4.3: 删除原第 8 条（"输出长度应与图像实际文字量匹配..."）
  - [x] SubTask 4.4: 保留原第 1-5 条（bbox、易混淆字形、藏文数字、藏文标点、分隔符），这些条目将通过 Task 2 新增的 `lang_hint` 注入机制在 DeepSeek-OCR 模式下生效

- [x] Task 5: 验证修复效果
  - [x] SubTask 5.1: 确认 `config.py` 修改后默认参数为 frequency_penalty=0.0, presence_penalty=0.0, temperature=0.1, max_tokens=8000
  - [x] SubTask 5.2: 确认 `DEEPSEEK_OCR_PROMPT` 不再包含被回显的英文短语
  - [x] SubTask 5.3: 确认 DeepSeek-OCR 分支调用 `_build_lang_hint()` 并将结果追加到 user 消息文本
  - [x] SubTask 5.4: 确认 VLM 分支也调用 `_build_lang_hint()`（共享逻辑，无重复实现）
  - [x] SubTask 5.5: 确认 `source_lang="bo"` 时 `lang_hint` 包含藏文 OCR 规则（bbox、易混淆字形、藏文数字、藏文标点、分隔符）和通用 OCR 规则
  - [x] SubTask 5.6: 确认 `.env.example` 注释与默认值一致
  - [x] SubTask 5.7: 确认 `bo_to_zh.py` OCR 规则不再包含防重复条目，且第 1-5 条保留完整

# Task Dependencies

- Task 1, 3, 4 互相独立，可并行执行
- Task 2 独立于 Task 1/3/4，可并行执行
- Task 5 依赖 Task 1-4 全部完成
