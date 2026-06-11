# Checklist

## OCR 模式章节关联

- [x] OCR 模式提取结果返回前执行了完整的章节关联流程
- [x] OCR 模式下文本块有正确的 `chapter_id` 和 `chapter_title`
- [x] OCR 模式下表格有正确的 `chapter_id` 和 `chapter_title`
- [x] OCR 模式下图像有正确的 `chapter_id` 和 `chapter_title`
- [x] 章节拆分的 Markdown 输出包含对应章节的所有内容（文本+表格+图像）
- [x] 分批 OCR 模式下章节关联正确执行

## 多表格 bbox 修复

- [x] 同一页多个表格各自获得独立的 bbox
- [x] 不再出现所有表格共享第一个表格 bbox 的情况

## 单元格 bbox 补充

- [x] OCR 模式下单元格 bbox 基于表格 bbox 等分计算
- [x] `PdfTable.row_heights` 和 `col_widths` 被正确填充
- [x] 表格 bbox 无效时单元格 bbox 保持 `(0,0,0,0)`

## PDF 表格渲染位置修复

- [x] OCR 模式表格在 PDF 中基于 bbox 等分渲染
- [x] 不再使用硬编码坐标 `x0=50+j*100, y0=200+i*30`
- [x] 表格渲染位置与原始表格区域对齐

## 表格翻译批量化

- [x] 表格翻译按行批量调用 API
- [x] 翻译结果正确拆分回各单元格
- [x] API 调用次数显著减少（从 N*M 减少到 N）
- [x] 包含特殊字符的单元格文本不会导致拆分错误

## Word 表格样式

- [x] Word 输出表格有可见边框
- [x] 单元格文本有合适的字体和字号

## Markdown 表格智能表头

- [x] 首行为表头时正常渲染
- [x] 首行非表头时添加空表头行

## 端到端验证

- [ ] OCR 模式含表格文档能正确识别、翻译、输出
- [ ] 非 OCR 模式含表格文档不受影响（回归测试）
- [ ] PDF/Word/Markdown 三种输出格式表格均正确
