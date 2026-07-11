# Tasks

- [x] Task 1: 在 `services/translation_content.py` 中添加异常输出检测方法 `_is_translation_garbage`
  - [x] SubTask 1.1: 实现长度膨胀检测：译文长度 > 原文长度 × 5 时返回 True
  - [x] SubTask 1.2: 实现重复模式检测：同一子串连续重复 > 10 次时返回 True
  - [x] SubTask 1.3: 方法返回 (is_garbage, reason) 元组，便于日志记录

- [x] Task 2: 在 `translate_merged_block` 方法中集成异常检测和回退
  - [x] SubTask 2.1: 在获取翻译结果后、创建 MergedBlock 前，调用 `_is_translation_garbage`
  - [x] SubTask 2.2: 检测到垃圾输出时，记录 WARNING 日志并回退使用原文
  - [x] SubTask 2.3: 截断检测（truncated）后，也调用异常检测

- [x] Task 3: 在 `translate_original_block` 方法中集成异常检测和回退
  - [x] SubTask 3.1: 在获取翻译结果后、创建 TextBlock 前，调用 `_is_translation_garbage`
  - [x] SubTask 3.2: 检测到垃圾输出时，记录 WARNING 日志并回退使用原文
  - [x] SubTask 3.3: 截断检测（truncated）后，也调用异常检测

# Task Dependencies

- Task 2 和 Task 3 依赖 Task 1（先实现检测方法再集成）
