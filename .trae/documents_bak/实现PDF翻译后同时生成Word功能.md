# 实现PDF翻译后支持选择输出格式功能（PDF/Word）

## 1. 技术选型

- **Word生成**：使用 `python-docx` 库直接生成Word文档
- **图像提取**：使用 `PyMuPDF` 扩展现有PDF提取器，添加图像提取功能

## 2. 实现步骤

### 2.1 添加依赖

- 在 `requirements.txt` 中添加 `python-docx` 依赖

### 2.2 扩展PDF提取器

- 修改 `modules/pdf_extractor.py`，添加图像提取功能
- 在 `extract_text` 方法中添加图像提取逻辑
- 将提取的图像信息添加到 `PdfExtraction` 对象中

### 2.3 创建Word生成器

- 创建 `modules/docx_generator.py` 文件
- 实现 `DocxGenerator` 类，支持：
  - 文本内容生成（使用合并块中的文本和样式）
  - 表格生成
  - 图像插入
- 实现 `generate_docx` 方法，接收翻译后的内容、样式信息和图像信息

### 2.4 修改翻译服务

- 在 `translation_service.py` 中导入 `DocxGenerator`
- 修改 `process_translation` 方法，添加输出格式参数
- 根据输出格式参数决定生成PDF、Word或两者
- 保存合并后的翻译结果和样式信息
- 保存提取的图像信息
- 更新任务结果处理，支持返回对应格式的文件路径

### 2.5 更新前端界面

- 修改 `templates/index.html`，添加输出格式选择选项（PDF/Word/两者）
- 修改 `app.py`，处理输出格式选项的请求参数

## 3. 核心功能实现

### 3.1 图像提取功能

- 使用 PyMuPDF 的 `get_images()` 方法提取图像
- 保存图像到临时目录
- 记录图像的位置信息和页面编号

### 3.2 Word生成器的核心逻辑

- 使用 `python-docx` 创建新的Word文档
- 遍历翻译后的合并块，按页面组织内容
- 对于每个合并块：
  - 从合并块中获取样式信息（字体、大小、颜色等）
  - 在Word文档中应用对应的样式
  - 添加文本内容
- 按顺序插入图像
- 处理表格内容
- 保存生成的Word文档到输出目录

### 3.3 输出格式处理

- **PDF格式**：使用现有的 `PdfGenerator` 生成PDF
- **Word格式**：使用新的 `DocxGenerator` 生成Word
- **两者**：同时生成PDF和Word

## 4. 预期结果

- 用户可以选择输出格式：仅PDF、仅Word或两者
- 生成的Word文档包含与PDF相同的翻译内容
- Word文档保留原始PDF的文字样式和大小
- Word文档包含原始PDF中的图片
- 系统能够正确处理和返回对应格式的文件

## 5. 实现注意事项

- **样式映射**：确保PDF样式能够准确映射到Word样式
- **图像处理**：确保图像能够正确提取和插入到Word文档
- **性能优化**：处理大型文档时的性能考虑
- **格式一致性**：确保生成的文件与PDF在内容和样式上保持一致