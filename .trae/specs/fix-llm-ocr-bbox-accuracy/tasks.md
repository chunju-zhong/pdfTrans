# Tasks

- [ ] Task 1: 在 TextBlock 模型中添加 original_text 属性
  - [ ] 在 `models/text_block.py` 的 TextBlock 类中添加 `original_text` 属性，默认为 None
  - [ ] 确保属性在 `__init__` 中初始化

- [ ] Task 2: 在翻译服务中保存原始文本
  - [ ] 在 `services/translation_service.py` 中，翻译完成后将原始文本保存到 `full_block.original_text`
  - [ ] 仅对 LLM OCR 提取的文本块保存 original_text（非 LLM OCR 的块不需要）

- [ ] Task 3: 在 PDF 生成器中使用原始 PDF 实际位置
  - [ ] 在 `_draw_translated_text` 方法中，对有 `original_text` 的文本块，使用 `page.search_for(original_text)` 搜索实际位置
  - [ ] 如果搜索到结果，计算匹配区域的并集矩形作为实际 bbox
  - [ ] 使用实际 bbox 替换 OCR bbox，用于 redaction 和文本渲染
  - [ ] 使用实际 bbox 重新估算 font_size（`min(bbox_height * 0.75, 36)`）
  - [ ] 搜索失败时回退到 OCR bbox
  - [ ] 添加日志记录搜索结果

- [ ] Task 4: 重启服务器并验证
  - [ ] 重启 python app.py 加载新代码
  - [ ] 重新翻译第 5 页验证问题是否修复

# Task Dependencies
- Task 1 是 Task 2 的前置条件
- Task 2 是 Task 3 的前置条件
- Task 4 依赖 Task 1-3 全部完成
