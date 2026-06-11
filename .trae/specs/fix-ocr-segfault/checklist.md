# Checklist

- [x] app.py 中 `chapter_split` 参数正确传递到 `process_translation` 和 `extract_pdf_content`
- [x] translation_service.py 异步和同步方法均正确传递 `extract_chapter` 参数
- [x] `extract_chapter` 仅控制章节/书签提取，不影响 OCR 模型加载
- [x] OCR 模式下使用 PyMuPDF 直接提取 PDF 嵌入的原始图片（无需 OCR）
- [x] OCR 分步骤提取：步骤0（原始图片）-> 步骤1（版面分析+文本OCR）-> 释放 -> 步骤2（表格识别）-> 释放 -> 步骤3（公式识别）-> 释放 -> 步骤4（图表/印章裁剪）
- [x] 每步仅加载该步骤需要的模型，完成后 `del pipeline; gc.collect()` 释放内存
- [x] 所有内容类型（文本、表格、公式、图表、印章）都被识别，无需用户手动选择
- [x] 无表格/公式区域时跳过对应步骤，不加载模型
- [x] config.py 中移除 `OCR_USE_TABLE_RECOGNITION` 和 `OCR_USE_FORMULA_RECOGNITION`
- [x] PaddleOcrExtractor 不再接收功能开关参数
- [x] 每个步骤加载模型前检查可用内存，不足时跳过并降级处理
- [x] OCR 处理在独立子进程中运行，崩溃不影响 Flask 主进程
- [x] OCR 子进程崩溃后任务状态更新为错误，显示友好提示
- [x] OCR 子进程退出后释放所有模型内存和 IPC 资源
- [ ] 在 16GB Mac 上测试：OCR 模式不触发段错误（内存峰值 ~1400MB 而非 2700MB+）
