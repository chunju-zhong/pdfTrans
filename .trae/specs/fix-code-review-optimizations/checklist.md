# Checklist

## 补充捕获文本过滤逻辑提取

- [x] `_filter_uncovered_textlines` 静态方法已创建
- [x] `_process_page_layout` 补充捕获部分嵌套层级降低（5层→3层）
- [x] 过滤行为不变：有文本的 textline 保留，无文本的过滤并记录日志

## else 分支 TEXT_SKIP 日志

- [x] 未知标签分支 text 为空时记录 `[TEXT_SKIP]` WARNING 日志
- [x] 日志格式与 TEXT_LABELS 分支一致

## SHORT_TEXT_THRESHOLD 模块级常量

- [x] `SHORT_TEXT_THRESHOLD` 定义在 `text_analyzer.py` 模块顶部
- [x] `_add_similar_blocks` 引用模块级常量而非局部变量

## 日志标签修正

- [x] `rec_texts` 长度不匹配 WARNING 日志使用 `[OCR_WARN]` 标签
