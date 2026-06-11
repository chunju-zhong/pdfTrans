# Tasks

- [x] Task 1: 用 insert_pdf 替代 show_pdf_page 复制页面
  - [x] 1.1: 修改 `generate_pdf` 方法，将 `new_doc.new_page()` + `show_pdf_page()` 替换为 `new_doc.insert_pdf(original_doc, from_page=idx, to_page=idx)` + `new_doc[-1]`
  - [x] 1.2: 验证无翻译内容的页面也能正常复制

- [x] Task 2: 用 redaction 机制替代白色矩形遮盖
  - [x] 2.1: 重构 `_draw_translated_text` 为两遍遍历：第一遍添加 redaction 标注，第二遍插入翻译文本
  - [x] 2.2: 在两遍之间调用 `page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)` 一次性删除原文
  - [x] 2.3: 重构 `_draw_translated_table` 同样为两遍遍历：第一遍 redaction，第二遍插入文本+网格线
  - [x] 2.4: 确保 redaction 区域使用与白色矩形相同的 padding 逻辑

- [x] Task 3: 实现字体缓存
  - [x] 3.1: 修改 `_get_suitable_font` 方法，在查找前先检查 `self.font_cache` 中是否有 `(original_font, target_lang)` 的缓存
  - [x] 3.2: 查找成功后将 `(fontname, fontfile)` 存入缓存
  - [x] 3.3: 缓存命中时仍需调用 `page.insert_font()` 确保当前页面引用字体，但跳过文件系统查找和兼容性检测
  - [x] 3.4: 在 `generate_pdf` 开始时清空 `self.font_cache`，确保每次生成使用干净状态

- [x] Task 4: 保存时启用压缩优化
  - [x] 4.1: 将 `new_doc.save(output_pdf_path)` 改为 `new_doc.save(output_pdf_path, deflate=True, garbage=4, clean=True)`

# Task Dependencies
- Task 1 和 Task 2 必须一起完成，因为 `insert_pdf` 是 redaction 正常工作的前提（`show_pdf_page` 创建的 XObject 页面 redaction 可能不生效）
- Task 3 独立，可并行
- Task 4 独立，可并行
