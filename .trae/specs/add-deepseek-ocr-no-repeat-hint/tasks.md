# Tasks

- [x] Task 1: 重构 `_build_short_english_hint()` 方法，追加通用抑制重复提示
  - [x] SubTask 1.1: 将方法体改为先构建 `parts` 列表
  - [x] SubTask 1.2: `source_lang == "bo"` 时向 `parts` 追加藏文专项提示
  - [x] SubTask 1.3: 向 `parts` 追加通用提示 `"Do not repeat the same sentence."`
  - [x] SubTask 1.4: 返回 `" ".join(parts)`
- [x] Task 2: 验证 DeepSeek-OCR 分支调用逻辑未变
  - [x] SubTask 2.1: 确认 DeepSeek-OCR 分支仍为 `user_text = f"{DEEPSEEK_OCR_PROMPT} {short_hint}"`
  - [x] SubTask 2.2: 确认 short_hint 为空时回退逻辑未变（虽然现在总会有通用提示，但保留兜底）
- [x] Task 3: 验证 VLM 分支未受影响
  - [x] SubTask 3.1: 确认 VLM 分支仍使用 `_build_lang_hint()` 加载中文规则
- [ ] Task 4: 实际运行验证（用户验证）
  - [ ] SubTask 4.1: 运行藏文 OCR 任务（page 6-10），确认不再出现大量重复句子
  - [ ] SubTask 4.2: 确认 API 请求仍成功返回（HTTP 200，不因追加指令导致 500）

# Task Dependencies

- Task 2、Task 3 独立（仅验证未修改的代码）
- Task 4 依赖 Task 1 完成
