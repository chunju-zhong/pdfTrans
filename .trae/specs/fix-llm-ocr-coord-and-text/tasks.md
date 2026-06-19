# Tasks

- [x] Task 1: LLM OCR 像素坐标转 PDF 点坐标
  - [x] 在 `extract_from_pdf` 方法中，获取每页的 `page_width_pts`、`page_height_pts`、`img_width_px`、`img_height_px`
  - [x] 将页面尺寸信息传递给 `_extract_page` 方法
  - [x] 在 `_extract_page` 中传递给 `_parse_response` 及其子方法
  - [x] 在 `_parse_ref_tags_response` 和 `_parse_json_response` 中，使用缩放比例将像素 bbox 转换为 PDF 点坐标
  - [x] 图像块（PdfImage）的 bbox 也需要转换
  - [x] 添加 `_pixel_to_pdf_coords` 单元测试

- [x] Task 2: 清理 Markdown 标题前缀
  - [x] 在 `_parse_ref_tags_response` 中，对 `actual_text` 清理 `#`、`##`、`###` 等 Markdown 标题前缀
  - [x] 使用 `re.sub(r'^#{1,6}\s*', '', actual_text)` 清理前缀

- [x] Task 3: 验证 is_body_text=True 生效
  - [x] 确认 `_parse_ref_tags_response`、`_parse_json_response`、`_parse_markdown_response` 中所有文本块的 `is_body_text=True`
  - [x] 确认 OCR 模式下 `_finalize_extraction`（含 `mark_non_body_text`）不会被调用，不会覆盖 `is_body_text`
  - [x] 运行测试验证

- [x] Task 4: 重启服务器加载新代码
  - [x] 终止旧服务器进程
  - [x] 重新启动 python app.py

# Task Dependencies
- Task 2 和 Task 3 无依赖，可并行
- Task 1 需要修改方法签名，影响 Task 2 和 Task 3 的代码位置，建议先完成 Task 1
- Task 4 依赖 Task 1-3 代码修改完成
