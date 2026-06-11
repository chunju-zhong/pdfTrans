# Tasks

- [x] Task 1: 修复翻译服务保留所有页面
  - [x] SubTask 1.1: 在 `extract_pdf_content` 中收集所有页码 `all_page_nums` 并返回
  - [x] SubTask 1.2: 在 `_translate_content` 中接收 `all_page_nums` 参数，为无翻译文本块的页面创建空 PdfPage

- [x] Task 2: 修复 PDF 生成器包含所有原始页面
  - [x] SubTask 2.1: 修改页面处理逻辑，遍历原始 PDF 的所有页面而非仅翻译内容页面
  - [x] SubTask 2.2: 无翻译内容的页面直接复制原始页面
  - [x] SubTask 2.3: 用映射表替代线性搜索提升查找效率

- [x] Task 3: 添加版面分析调试日志
  - [x] SubTask 3.1: 在 `_process_page_layout` 中添加 `[LAYOUT_DEBUG]` 摘要日志

# Task Dependencies
- Task 1 和 Task 2 可并行
- Task 3 独立，可并行
