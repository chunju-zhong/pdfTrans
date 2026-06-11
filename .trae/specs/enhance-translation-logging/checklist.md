# Checklist

## FileHandler 即时刷新

- [x] `FileHandler` 在每次写入后刷新到磁盘
- [x] 翻译步骤的 INFO 日志能即时在 `app.log` 中看到

## 翻译步骤详细日志

- [x] 翻译 API 调用前记录原文前100字符
- [x] 翻译 API 调用后记录翻译结果前200字符
- [ ] 翻译 API 调用后记录 token 使用量
- [x] 翻译 API 异常时记录 ERROR 日志

## 翻译结果与原文相同检查

- [x] `translate_original_block` 中检查翻译结果与原文是否相同
- [x] `translate_merged_block` 中检查翻译结果与原文是否相同
- [x] 相同时记录 WARNING 日志
