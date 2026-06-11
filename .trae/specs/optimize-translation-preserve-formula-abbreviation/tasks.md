# Tasks

- [x] Task 1: TextBlock 新增 is_formula 属性
  - [x] SubTask 1.1: 在 TextBlock 类中新增 `is_formula` 属性，默认 `False`
  - [x] SubTask 1.2: 确认 TextBlock 的 `to_dict`/`from_dict` 等序列化方法兼容新属性

- [x] Task 2: OCR 提取时标记公式块
  - [x] SubTask 2.1: 在 `paddle_extractor.py` 的 `_process_page_formulas` 方法中，创建公式 TextBlock 时设置 `is_formula=True`

- [x] Task 3: 翻译服务跳过公式块
  - [x] SubTask 3.1: 在 `translation_service.py` 的文本块翻译循环中，`is_formula=True` 的块跳过翻译，直接使用原文
  - [x] SubTask 3.2: 确认跳过的公式块仍被包含在最终翻译结果中（用于 PDF 渲染）

- [x] Task 4: 翻译提示词新增公式和缩写保护规则
  - [x] SubTask 4.1: 在 `translator.py` 的 `_generate_system_prompt` 方法中，新增"不翻译公式"规则（仿照规则10/11的格式）
  - [x] SubTask 4.2: 新增"不解释缩写"规则

# Task Dependencies
- Task 1 → Task 2 → Task 3 顺序执行
- Task 4 独立，与 Task 1-3 并行
