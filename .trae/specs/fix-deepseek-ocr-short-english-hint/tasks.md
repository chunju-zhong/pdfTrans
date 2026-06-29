# Tasks

- [x] Task 1: 在 `LlmOcrExtractor` 类中新增 `_build_short_english_hint()` 方法
  - [x] SubTask 1.1: 在 `_build_lang_hint()` 方法之后新增 `_build_short_english_hint(self) -> str` 方法
  - [x] SubTask 1.2: 方法内根据 `self.source_lang` 返回简短纯英文提示（仅 ASCII 字符）
  - [x] SubTask 1.3: `source_lang == "bo"` 时返回 `"For Tibetan: keep full line bbox width, preserve Tibetan numerals and punctuation, retain ||| separators."`
  - [x] SubTask 1.4: 未知语言返回空字符串 `""`
- [x] Task 2: 修改 DeepSeek-OCR 分支的 prompt 构建逻辑
  - [x] SubTask 2.1: 将 `lang_hint = self._build_lang_hint()` 替换为 `short_hint = self._build_short_english_hint()`
  - [x] SubTask 2.2: 将 `user_text = f"<image>\n{lang_hint}<|grounding|>Convert the document to markdown."` 替换为 `user_text = f"{DEEPSEEK_OCR_PROMPT} {short_hint}"`
  - [x] SubTask 2.3: 更新注释，说明使用纯英文提示避免藏文 Unicode 导致 500 错误
- [x] Task 3: 验证 VLM 分支未受影响
  - [x] SubTask 3.1: 确认 VLM 分支（else 分支）仍使用 `_build_lang_hint()` 加载中文规则
  - [x] SubTask 3.2: 确认 VLM 分支 user_text 格式未变（`f"{lang_hint}请提取第{page_num}页..."`）
- [ ] Task 4: 实际运行验证（用户验证）
  - [ ] SubTask 4.1: 运行藏文 OCR 任务（page 6-10），确认不再出现 HTTP 500
  - [ ] SubTask 4.2: 确认 prompt tokens 数量在合理范围（与旧版 819 tokens 接近或略增）

# Task Dependencies

- Task 2 依赖 Task 1（需要调用 `_build_short_english_hint()`）
- Task 3 独立（仅验证未修改的代码）
- Task 4 依赖 Task 1、2 完成
