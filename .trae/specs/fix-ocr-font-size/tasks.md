# Tasks

- [x] Task 1: 改进字体大小估算算法
  - [x] SubTask 1.1: 在 `_process_page_layout` 中，从 result 获取 `overall_ocr_res`，提取 `rec_boxes`（textline 级别的 bbox）
  - [x] SubTask 1.2: 对每个 TEXT_LABELS 的 block，找到落在该 block bbox 范围内的 textline，用 textline bbox 高度平均值 * 0.75 估算字体大小
  - [x] SubTask 1.3: 添加回退逻辑：如果 `overall_ocr_res` 不可用，使用 `LayoutBlock.num_of_lines` 或 `LayoutBlock.text_line_height`；如果都不可用，使用 `bbox_height * 0.75`
  - [x] SubTask 1.4: 将字体大小上限从 20pt 提高到 36pt
  - [x] SubTask 1.5: 同步修改公式识别中的字体大小估算，上限从 16pt 提高到 36pt，系数从 0.6 改为 0.75
  - [x] SubTask 1.6: 增强 FONT_DEBUG 日志，输出 textline_count、avg_textline_height、num_of_lines、text_line_height 等中间值

# Task Dependencies
无
