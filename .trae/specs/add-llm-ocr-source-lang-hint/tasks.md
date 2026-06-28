# Tasks

- [x] Task 1: 新增模块级常量 `_SOURCE_LANG_ENGLISH_NAMES`
  - [x] SubTask 1.1: 在 `modules/ocr/llm_extractor.py` 模块级（`VLM_JSON_SYSTEM_PROMPT` 之后）新增字典
  - [x] SubTask 1.2: 覆盖 9 种语言：zh→Chinese、en→English、ja→Japanese、ko→Korean、fr→French、de→German、es→Spanish、ru→Russian、bo→Tibetan
- [x] Task 2: 修改 `_build_short_english_hint()` 方法，在开头追加语言类型提示
  - [x] SubTask 2.1: 在 `parts` 列表开头追加 `f"The document is primarily in {lang_name}."`（lang_name 来自 `_SOURCE_LANG_ENGLISH_NAMES`）
  - [x] SubTask 2.2: 使用 `self.source_lang or ''` 兜底 None 情况
  - [x] SubTask 2.3: 未知语言时不追加语言提示，保持原有行为
- [x] Task 3: 修改 VLM 分支 user_text，追加中文语言类型提示
  - [x] SubTask 3.1: 从 `config.SUPPORTED_LANGUAGES` 获取中文名称
  - [x] SubTask 3.2: 拼接 `lang_prefix = f"该文档主要语言为{lang_name_zh}。" if lang_name_zh else ''`
  - [x] SubTask 3.3: user_text 改为 `f"{lang_hint}{lang_prefix}请提取第{page_num}页PDF中的所有文字、表格和图表信息。"`
- [x] Task 4: 验证 DeepSeek-OCR 分支调用逻辑未变
  - [x] SubTask 4.1: 确认仍为 `user_text = f"{DEEPSEEK_OCR_PROMPT} {short_hint}"`
- [ ] Task 5: 实际运行验证（用户验证）
  - [ ] SubTask 5.1: 运行藏文 OCR 任务，确认 prompt 包含 "The document is primarily in Tibetan."
  - [ ] SubTask 5.2: 确认 API 请求成功返回（HTTP 200）

# Task Dependencies

- Task 2 依赖 Task 1（需要 `_SOURCE_LANG_ENGLISH_NAMES` 常量）
- Task 3 独立（VLM 分支使用 `config.SUPPORTED_LANGUAGES`，不依赖新常量）
- Task 4、Task 5 依赖 Task 1、2、3 完成
