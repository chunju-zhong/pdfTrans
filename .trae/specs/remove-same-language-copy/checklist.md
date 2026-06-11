# Checklist

## 移除同语言早期返回

- [x] `process_translation()` 中不再有 `source_lang == target_lang` 的早期返回
- [x] `process_translation_sync()` 中不再有 `source_lang == target_lang` 的早期返回

## 删除 handle_same_language()

- [x] `handle_same_language()` 方法已删除
- [x] 代码中无残留的 `handle_same_language` 调用

## 端到端验证

- [ ] 源语言=目标语言 + PDF 输出：正常提取并生成 PDF（非直接拷贝）
- [ ] 源语言=目标语言 + Word 输出：正常生成 .docx 文件
- [ ] 源语言=目标语言 + Markdown 输出：正常生成 .md 文件
- [ ] 源语言≠目标语言：行为不受影响（回归测试）
