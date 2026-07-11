# Tasks

- [x] Task 1: 增强 `_is_translation_unchanged` 方法，添加高相似度未翻译检测
  - [x] SubTask 1.1: 实现 `_normalize_for_comparison` 辅助方法，去除断字标记（`‐\n`、`-\n`、连字符后换行）和多余空白
  - [x] SubTask 1.2: 实现 `_calculate_similarity` 辅助方法，对两个字符串进行字符级相似度比较（最长公共子序列 / 简单字符集交集）
  - [x] SubTask 1.3: 实现 `_contains_target_language_chars` 辅助方法，检测文本是否包含目标语言字符（默认检测中文 \u4e00-\u9fff）
  - [x] SubTask 1.4: 在 `_is_translation_unchanged` 中添加第三种检测：去除断字后相似度 > 85% 且不含目标语言字符 → 返回 True

- [x] Task 2: 在 `translate_merged_block` 中集成未翻译检测和重试逻辑
  - [x] SubTask 2.1: 将现有 `_is_translation_unchanged` WARNING 日志后的逻辑改为：检测到未翻译时执行一次重试翻译
  - [x] SubTask 2.2: 重试时在用户消息前追加强调指令（"【重要】请将以下文本翻译为{target_lang}，不要返回原文："）
  - [x] SubTask 2.3: 重试结果仍为未翻译时，回退使用原文并记录 WARNING（含原文长度、译文长度、相似度、重试状态）

- [x] Task 3: 在 `translate_original_block` 中集成未翻译检测和重试逻辑
  - [x] SubTask 3.1: 在 `translate_original_block` 中 LLM 返回结果后，调用 `_is_translation_unchanged`
  - [x] SubTask 3.2: 检测到未翻译时执行一次重试翻译（与合并块逻辑一致）
  - [x] SubTask 3.3: 重试结果仍为未翻译时，回退使用原文并记录 WARNING

# Task Dependencies

- Task 2 和 Task 3 依赖 Task 1（先增强检测方法再集成重试逻辑）
- Task 2 和 Task 3 可以并行实现
