# Tasks

- [x] Task 1: 重排 DeepSeek-OCR 分支 prompt 结构，将 lang_hint 插入 `<|grounding|>` 之前
  - [x] SubTask 1.1: 在 `modules/ocr/llm_extractor.py` 的 `_extract_page` 方法中，定位 DeepSeek-OCR 分支（`if use_deepseek_prompt:` 块，约第 340-360 行）
  - [x] SubTask 1.2: 保留 `lang_hint = self._build_lang_hint()` 调用
  - [x] SubTask 1.3: 将 `user_text = DEEPSEEK_OCR_PROMPT + lang_hint` 改为条件构建：当 `lang_hint` 非空时使用 `f"<image>\n{lang_hint}<|grounding|>Convert the document to markdown."`，否则使用 `DEEPSEEK_OCR_PROMPT`
  - [x] SubTask 1.4: 添加注释说明将 lang_hint 插入 `<|grounding|>` 之前的原因（保持原生指令不被破坏）

- [x] Task 2: 验证 VLM 分支未被修改
  - [x] SubTask 2.1: 确认 VLM 分支（`else:` 块）仍调用 `_build_lang_hint()`
  - [x] SubTask 2.2: 确认 VLM 分支的 `user_text` 仍为 `f"{lang_hint}请提取第{page_num}页PDF中的所有文字、表格和图表信息。"`
  - [x] SubTask 2.3: 确认 VLM 分支的 system 消息仍为 `VLM_JSON_SYSTEM_PROMPT`

- [x] Task 3: 验证修复效果
  - [x] SubTask 3.1: 确认 DeepSeek-OCR 分支在 `lang_hint` 非空时使用 `f"<image>\n{lang_hint}<|grounding|>Convert the document to markdown."`
  - [x] SubTask 3.2: 确认 DeepSeek-OCR 分支在 `lang_hint` 为空时使用 `DEEPSEEK_OCR_PROMPT`（fallback）
  - [x] SubTask 3.3: 确认 `lang_hint` 位于 `<image>` 之后、`<|grounding|>` 之前
  - [x] SubTask 3.4: 确认 `<|grounding|>Convert the document to markdown.` 保持原生格式不变
  - [x] SubTask 3.5: 确认 `_build_lang_hint` 方法仍然存在且逻辑未被修改
  - [x] SubTask 3.6: 确认参数修改保持不变（temperature=0.1, max_tokens=8000, frequency_penalty=0.0, presence_penalty=0.0）
  - [x] SubTask 3.7: 确认 `DEEPSEEK_OCR_PROMPT` 常量保持简化版本
  - [x] SubTask 3.8: 确认 `bo_to_zh.py` OCR 规则未被修改

# Task Dependencies

- Task 2 和 Task 3 可与 Task 1 并行验证（但 Task 1 需先完成代码修改）
- Task 3 依赖 Task 1 和 Task 2 完成
