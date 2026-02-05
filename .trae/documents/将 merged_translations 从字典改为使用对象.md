# 将 merged_translations 从字典改为使用 MergedBlock 对象

## 问题分析
目前 `merged_translations` 是一个字典列表，每个字典包含翻译后的文本和样式信息。用户要求将其改为使用现有的 `MergedBlock` 对象，直接将翻译后的文本更新到 `block_text` 属性。

## 实现方案

### 1. 更新 translation_service.py
- 修改 `process_merged_blocks` 方法，创建新的 `MergedBlock` 对象并将翻译后的文本设置为 `block_text`
- 修改 `process_original_blocks` 方法，创建新的 `MergedBlock` 对象并将翻译后的文本设置为 `block_text`
- 确保所有相关代码都使用 `MergedBlock` 对象的属性访问

### 2. 更新 docx_generator.py
- 修改 `generate_docx` 方法，使用 `MergedBlock` 对象的属性访问
- 确保所有字典访问都改为对象属性访问，特别是 `item['text']` 改为 `item.block_text`

### 3. 测试和验证
- 运行 GetDiagnostics 工具检查语法和类型错误
- 确保代码能够正常运行

## 具体修改点

1. **services/translation_service.py**：
   - 修改 `process_merged_blocks` 方法中的 `merged_translations.append` 调用，创建新的 `MergedBlock` 对象
   - 修改 `process_original_blocks` 方法中的 `merged_translations.append` 调用，创建新的 `MergedBlock` 对象
   - 确保所有相关代码使用对象属性访问

2. **modules/docx_generator.py**：
   - 修改 `generate_docx` 方法中处理 `merged_translations` 的代码
   - 将 `item['text']` 改为 `item.block_text`
   - 将其他字典访问改为对象属性访问

## 预期效果
- `merged_translations` 变为 `MergedBlock` 对象列表
- 所有相关代码使用对象属性访问，不再使用字典访问
- 保持与现有功能的兼容性
- 代码更加清晰和一致