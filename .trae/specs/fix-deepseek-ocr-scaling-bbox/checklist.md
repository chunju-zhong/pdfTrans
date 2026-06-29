# 检查清单：修复 DeepSeek-OCR 文本框位置偏移

## 代码实现检查

- [ ] 已定义 `OcrBlock` 数据类，包含 text、bbox、block_type、is_image、table_html、bboxes 字段
- [ ] 已定义 `BLOCK_TYPE_MAP` 映射，支持 title、text、header、footer、footnote、image 等类型
- [ ] 已实现 `_parse_response` 方法，支持三种格式（ref 标签、JSON、Markdown）带回退解析
- [ ] 已实现 `_parse_ref_tags_to_blocks` 方法，正确解析 DeepSeek-OCR 的 `<|ref|>` 标签格式
- [ ] 已实现 `_parse_ref_tag_bbox` 方法，从 `<|ref|>` 标签中提取 bbox 坐标
- [ ] 已实现 `_extract_json` 方法，支持从响应文本中提取 JSON（含代码块提取）
- [ ] 已实现 `_parse_json_to_blocks` 方法，将 JSON 格式响应解析为 OcrBlock 列表
- [ ] 已实现 `_parse_markdown_to_blocks` 方法，将 Markdown 段落解析为 OcrBlock 列表
- [ ] 已实现 `_map_ocr_blocks_to_models` 方法，将 OcrBlock 映射为 TextBlock/PdfTable/PdfImage
- [ ] 已实现 `_create_text_block` 方法，正确创建 TextBlock 并设置属性
- [ ] 已实现 `_create_table` 方法，正确创建 PdfTable 并设置属性
- [ ] 已实现 `_create_image` 方法，正确创建 PdfImage 并设置属性
- [ ] 已实现 `_detect_formula` 方法，正确检测纯 LaTeX 公式
- [ ] 已实现 `_estimate_font_size` 方法，根据 bbox 和文本长度估算字体大小
- [ ] 已实现 `_pixel_to_pdf_coords` 方法，支持归一化坐标和像素坐标转换
- [ ] 已实现 `_detect_image_margins` 方法，正确检测图像白边
- [ ] 已在 `llm_extractor.py` 中调用白边检测，并将内容区域信息加入 `page_info`

## 功能验证检查

- [ ] ref 标签格式解析：能正确解析 `<|ref|>坐标<|/ref|>` 格式的 bbox
- [ ] JSON 格式解析：能正确解析标准 JSON 和 markdown 代码块中的 JSON
- [ ] Markdown 格式解析：能正确解析标题、正文、图片等 Markdown 元素
- [ ] 坐标转换（无白边）：`pdf = normalized / 999 * page_size`
- [ ] 坐标转换（有白边）：`pdf = content_offset + normalized / 999 * content_size`
- [ ] 公式检测：能正确识别 `$...$`、`$$...$$`、`\(...\)`、`\[...\]` 等公式定界符
- [ ] 字体估算：能根据 bbox 高度和文本长度合理估算字体大小

## 调试日志检查

- [ ] 日志记录页面尺寸和图像尺寸
- [ ] 日志记录白边检测结果（像素数和百分比）
- [ ] 日志记录内容区域 PDF 坐标
- [ ] 日志记录示例归一化坐标及转换后 PDF 坐标
- [ ] 日志记录公式检测结果

## 回归测试检查

- [ ] 英文 PDF 页面无回归问题
- [ ] 藏文 PDF 页面无回归问题
- [ ] 中文 PDF 页面无回归问题
- [ ] 无白边的 PDF 页面使用原有逻辑（无回归）

## 单元测试检查

- [ ] 测试 ref 标签格式解析（正常情况）
- [ ] 测试 ref 标签格式解析（空 bbox）
- [ ] 测试 JSON 格式解析（标准 JSON）
- [ ] 测试 JSON 格式解析（markdown 代码块）
- [ ] 测试 Markdown 格式解析（标题）
- [ ] 测试 Markdown 格式解析（正文）
- [ ] 测试坐标转换（无白边）
- [ ] 测试坐标转换（有白边）
- [ ] 测试公式检测（纯公式）
- [ ] 测试公式检测（混合文本）

## 集成测试检查

- [ ] 使用实际 PDF 页面测试完整流程
- [ ] 验证文本框位置准确性（与原文对齐）
- [ ] 验证文本框大小准确性
