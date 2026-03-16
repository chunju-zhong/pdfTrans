# 文档更新计划

## 1. 代码变更分析

### 1.1 变更识别

**已修改的文件（8个）：**
1. `modules/extractors/__init__.py` - 添加 extract_tables_by_pymupdf 导出
2. `modules/extractors/table_processor.py` - 添加 PyMuPDF 表格提取函数和日志
3. `modules/pdf_extractor.py` - 添加 table_extractor 参数
4. `modules/pdf_generator.py` - 添加表格绘制日志
5. `services/translation_service.py` - 添加表格翻译日志和 UI 文本注释
6. `static/js/main.js` - UI 注释修改
7. `templates/index.html` - UI 文本修改
8. `utils/logging_config.py` - 日志级别调整

**新增的文件（4个）：**
1. `.trae/documents/rename_chapter_split_ui.md` - 计划文件
2. `.trae/specs/pymupdf_table_extraction/` - PyMuPDF 表格提取规格文档
3. `.trae/specs/table_cell_translation_debug/` - 表格单元格翻译诊断规格文档
4. `tests/test_pymupdf_table_extraction.py` - PyMuPDF 表格提取测试

### 1.2 变更类型分析

| 变更类型 | 文件 | 说明 |
|---------|------|------|
| 新功能添加 | table_processor.py, pdf_extractor.py, __init__.py | PyMuPDF 表格提取功能 |
| UI/UX改进 | main.js, index.html, translation_service.py | "按章节拆分Markdown"改为"按章节翻译Markdown" |
| 错误修复 | table_processor.py | 修复 bbox 类型判断问题 |
| 日志增强 | translation_service.py, pdf_generator.py | 添加表格翻译和绘制调试日志 |
| 代码优化 | logging_config.py | 日志级别从 DEBUG 调整为 INFO |

### 1.3 变更影响评估

- **功能影响**：新增 PyMuPDF 表格提取方法，用户可选择使用 Camelot 或 PyMuPDF
- **文档影响**：需要更新 UI 相关文档，说明新的表格提取选项
- **测试影响**：添加了新的测试文件
- **兼容性影响**：新增 table_extractor 参数，默认使用 PyMuPDF，不影响现有功能

## 2. 文档更新范围

根据 update_doc.md 指南，需要更新以下文档：

### 2.1 README.md
- 添加开发记录：PyMuPDF 表格提取功能实现
- 添加开发记录：UI 文本优化

### 2.2 AI开发进度 (.trae/documents/ai_dev_progress.md)
- 添加最新开发进度记录

### 2.3 TODO.md
- 检查是否需要更新任务列表

## 3. 实施步骤

### 3.1 准备阶段
- [x] 收集变更信息（已完成）
- [x] 分析变更影响（已完成）
- [x] 确定更新范围（已完成）

### 3.2 执行阶段
- [ ] 更新 README.md 开发记录
- [ ] 更新 AI开发进度文档
- [ ] 检查 TODO.md 是否需要更新

### 3.3 验证阶段
- [ ] 格式检查
- [ ] 内容验证
- [ ] 顺序检查（时间逆序）

## 4. 更新内容草稿

### README.md 开发记录草稿
```markdown
### 2026-03-12
- **新功能**：
  - 实现 PyMuPDF 表格提取功能，添加 extract_tables_by_pymupdf 函数
  - 在 PdfExtractor 中添加 table_extractor 参数，支持选择 Camelot 或 PyMuPDF
  - 修复 PyMuPDF 表格提取时 bbox 类型判断问题
- **UI优化**：
  - 将"按章节拆分Markdown"修改为"按章节翻译Markdown"
  - 优化提示文本为"启用后按章节拆分翻译并生成多个Markdown文件"
- **日志增强**：
  - 在 translation_service.py 中添加表格翻译详细日志
  - 在 pdf_generator.py 中添加表格绘制日志，便于调试
  - 调整日志级别从 DEBUG 为 INFO
- **相关文件**：
  - modules/extractors/table_processor.py
  - modules/pdf_extractor.py
  - modules/pdf_generator.py
  - services/translation_service.py
  - templates/index.html
```

### AI开发进度记录草稿
```markdown
### 2026-03-12
- **当前状态**：完成 PyMuPDF 表格提取功能开发和 UI 文本优化
- **已完成任务**：
  - 实现 PyMuPDF 表格提取功能：
    - 在 table_processor.py 中添加 extract_tables_by_pymupdf 函数
    - 使用 PyMuPDF 的 find_tables() 方法提取表格
    - 保持与 extract_tables_by_camelot 相同的参数和返回值格式
    - 修复 bbox 类型判断问题
  - 集成到 PdfExtractor：
    - 添加 table_extractor 参数，默认使用 PyMuPDF
    - 在 __init__.py 中导出新函数
  - UI 文本优化：
    - 修改 index.html 中的复选框标签和提示文本
    - 修改 main.js 中的相关注释
    - 修改 translation_service.py 中的参数注释
  - 日志增强：
    - 在表格翻译流程中添加详细日志
    - 在表格绘制流程中添加调试日志
- **技术实现**：
  - 使用 PyMuPDF 库进行表格提取
  - 使用异步任务池进行单元格翻译
  - 使用线程锁保证结果存储的线程安全
- **影响**：
  - 提供替代的表格提取方法，减少对 Camelot 的依赖
  - 改善 UI 文本准确性，提升用户体验
  - 增强调试能力，便于定位问题
- **遇到的问题**：
  - PyMuPDF bbox 可能返回元组或 Rect 对象，已添加类型判断处理
  - 表格单元格翻译日志诊断
- **后续计划**：
  - 完善测试用例
  - 优化其他 UI 文本
```
