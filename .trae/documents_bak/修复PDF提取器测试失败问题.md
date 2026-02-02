# 修复PDF提取器测试失败问题

## 问题分析

根据回归测试结果，PDF提取器模块有以下问题导致测试失败：

### 1. 缺少 `get_metadata` 方法
- 多个测试用例调用了 `pdf_extractor.get_metadata()` 方法，但该方法在当前实现中不存在
- 失败的测试用例：
  - `test_extract_page_text`
  - `test_extract_page_text_invalid_page`
  - `test_extract_tables_with_pages`
  - `test_get_metadata`
  - `test_get_metadata_invalid_file`

### 2. 异常处理问题
- 在 `table_processor.py` 中，当PDF文件不存在时，抛出的是通用 `Exception` 而不是 `FileNotFoundError`
- 失败的测试用例：
  - `test_extract_tables_invalid_file`

## 修复计划

### 1. 添加 `get_metadata` 方法
在 `PdfExtractor` 类中添加 `get_metadata` 方法，用于提取PDF的元数据，包括：
- 检查文件是否存在
- 使用 PyMuPDF 打开PDF文件
- 提取元数据信息
- 处理异常情况

### 2. 修复异常处理逻辑
修改 `table_processor.py` 中的异常处理逻辑：
- 在尝试打开文件前检查文件是否存在
- 如果文件不存在，直接抛出 `FileNotFoundError`
- 对于其他异常，保持当前的异常处理逻辑

## 预期效果

修复后，所有6个失败的测试用例应该能够通过，同时保持其他测试用例的通过率。

## 技术实现要点

1. **`get_metadata` 方法实现**：
   - 使用 `os.path.exists()` 检查文件是否存在
   - 使用 `fitz.open()` 打开PDF文件
   - 提取 `doc.metadata` 中的元数据信息
   - 处理文件不存在和其他异常情况

2. **异常处理修复**：
   - 在 `extract_tables` 函数开始处添加文件存在性检查
   - 如果文件不存在，直接抛出 `FileNotFoundError`
   - 保持其他异常的处理逻辑不变