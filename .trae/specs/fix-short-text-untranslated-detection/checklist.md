# Checklist
- [x] aiping `temperature` 已从 0.7 改为 0.1，`top_p` 从 0.8 改为 0.9
- [x] `_is_translation_unchanged()` 辅助函数已实现并能正确识别 `|||` 包装的未翻译文本
- [x] `translate_original_block()` 使用新检测逻辑，日志可观察到 WARNING
- [x] `translate_merged_block()` 使用新检测逻辑，日志可观察到 WARNING
- [x] 单元测试覆盖：`|||`包装未翻译、正常翻译、含`|||`的正常翻译三种场景
- [x] 现有测试不受影响（回归测试通过）
