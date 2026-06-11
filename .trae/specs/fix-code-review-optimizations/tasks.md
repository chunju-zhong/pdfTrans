# Tasks

- [x] Task 1: 提取补充捕获文本过滤逻辑为独立函数
  - [x] SubTask 1.1: 在 `PaddleOcrExtractor` 中添加 `_filter_uncovered_textlines` 静态方法，接收 `uncovered_textlines` 和 `has_textline_texts`，返回过滤后的列表
  - [x] SubTask 1.2: 在 `_process_page_layout` 的补充捕获部分调用新方法，替换内联的过滤逻辑，降低嵌套层级

- [x] Task 2: else 分支添加 TEXT_SKIP 日志
  - [x] SubTask 2.1: 在 `paddle_extractor.py` 的 `else`（未知标签）分支中，当 `text.strip()` 为空时添加 `[TEXT_SKIP]` WARNING 日志

- [x] Task 3: SHORT_TEXT_THRESHOLD 提升为模块级常量
  - [x] SubTask 3.1: 在 `text_analyzer.py` 模块顶部定义 `SHORT_TEXT_THRESHOLD = 20`
  - [x] SubTask 3.2: 修改 `_add_similar_blocks` 函数引用模块级常量

- [x] Task 4: rec_texts 长度不匹配日志标签修正
  - [x] SubTask 4.1: 将 `rec_texts` 长度不匹配 WARNING 日志的 `[FONT_DEBUG]` 改为 `[OCR_WARN]`

# Task Dependencies

- 所有任务相互独立，可并行
