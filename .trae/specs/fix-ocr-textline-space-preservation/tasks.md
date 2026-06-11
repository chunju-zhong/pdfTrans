# Tasks

- [x] Task 1: 从 overall_ocr_res 中提取 rec_text 并构建 textline 文本映射
  - [x] SubTask 1.1: 在 `_process_page_layout` 中，从 `overall_ocr_res` 同时提取 `rec_text`（与 `rec_boxes` 对应），构建 textline 级别的 (bbox, text) 列表
  - [x] SubTask 1.2: 对每个 block，找到落在其 bbox 范围内的 textline，按 y 坐标排序后拼接 rec_text，用拼接结果替代 block.content
  - [x] SubTask 1.3: 当 overall_ocr_res 不可用或匹配不到 textline 时，保留 block.content 作为 fallback

# Task Dependencies

（无依赖关系，Task 1 内部子任务按顺序执行）
