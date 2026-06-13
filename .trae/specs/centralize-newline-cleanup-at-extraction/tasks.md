# Tasks

- [x] Task 1: OCR 提取统一替换换行符
  - 修改 `modules/ocr/paddle_extractor.py` 的 `_build_text_from_textlines`，将换行符替换从"仅标题"改为"所有文本"通用处理
  - 移除 `is_title` 参数的条件判断，对所有文本执行 `replace('\n', '')`
  - 更新日志记录

- [x] Task 2: PDF 提取添加换行符替换
  - 在 `modules/pdf_extractor.py` 的 `_extract_text_blocks` 中，创建 TextBlock 后添加换行符替换逻辑
  - 对所有文本执行 `text.replace('\n', '')`

- [x] Task 3: 表格文本添加换行符删除
  - 检查 OCR 表格（`paddle_extractor.py` HTML解析）和 PDF 表格（`extract_tables_by_pymupdf`）的单元格文本
  - 在单元格文本创建时统一删除换行符

- [x] Task 4: 简化翻译阶段换行符处理
  - 修改 `modules/translator.py`：
    - 简化 `_preprocess_text`：移除 `text.split('\n')` 按行分割逻辑，保留基本 strip
    - 简化 `_postprocess_text`：同理移除 `\n` 相关处理
    - 删除系统提示词第7条"保持换行符一致性"规则（第154-158行）

- [x] Task 5: 更新 CHANGELOG
  - 更新 `CHANGELOG.zh.md` 和 `CHANGELOG.md` 中关于换行符处理的条目

- [x] Task 6: 运行测试验证
  - `test_newline_preservation.py` 14 个测试全部通过
  - `test_translator.py`, `test_aiping_translator.py`, `test_silicon_flow_translator.py` 共 30 个测试全部通过

# Task Dependencies
- Task 3 需先确认表格单元格文本创建的具体代码
- [Task 1, Task 2] 无依赖，可并行
- [Task 4, Task 5] 可在 Task 1-3 完成后并行
