# 更新 PDF 提取器调用方法，不再使用全局实例

## 问题分析

当前代码库中使用了全局的 `pdf_extractor` 实例，这不利于代码的模块化和可测试性。根据最新的优化，我们需要更新所有调用 `pdf_extractor` 的地方，改为使用本地实例。

## 计划内容

### 1. 修改 services/translation\_service.py 文件

* **修改导入语句**：将 `from modules.pdf_extractor import pdf_extractor` 改为 `from modules.pdf_extractor import PdfExtractor`

* **创建本地实例**：在使用 `pdf_extractor` 的地方，创建本地实例 `pdf_extractor = PdfExtractor(input_filepath)`

* **更新调用方式**：修改方法调用，移除 `pdf_path` 参数，例如：`extracted_content = pdf_extractor.extract_text(pages=list(target_pages))`

### 2. 移除全局实例

* **修改 modules/pdf\_extractor.py 文件**：移除文件末尾的 `pdf_extractor = PdfExtractor()` 这一行，因为我们不再使用它

## 具体修改点

### services/translation\_service.py

1. **第6行**：修改导入语句
2. **第121行**：创建本地实例并调用 `extract_text` 方法
3. **第190行**：创建本地实例并调用 `extract_text` 方法

### modules/pdf\_extractor.py

1. **第546行**：移除全局实例的创建

## 预期结果

* 所有代码不再使用全局的 `pdf_extractor` 实例

* 所有调用都使用本地创建的 `PdfExtractor` 实例

* 代码更加模块化和可测试

* 所有测试仍然通过

