# Tasks

- [ ] Task 1: 在 `_clean_latex` 中增加 OCR 误识别修复逻辑
  - [ ] SubTask 1.1: 添加 regex 规则：`(\d+\.?\d*)\^{\{\*\}\}` → `\1 \cdot`，修复数字后 `^{*}` 被误识别为乘法的问题
  - [ ] SubTask 1.2: 确保规则仅匹配数字后的 `^{*}`，不修改变量/括号后的 `^{*}`

- [ ] Task 2: 验证
  - [ ] SubTask 2.1: 语法检查（`python -m py_compile modules/ocr/paddle_extractor.py`）
  - [ ] SubTask 2.2: 现有测试通过
  - [ ] SubTask 2.3: 验证 latex2mathml 转换结果中 `0.6^{*}` 已被修正为 `0.6 \cdot`（无 `<msup>` 结构）
  - [ ] SubTask 2.4: 端到端验证：翻译包含 `0.6^{*}` 模式的 PDF，检查 DOCX 中常数可见

# Task Dependencies

无