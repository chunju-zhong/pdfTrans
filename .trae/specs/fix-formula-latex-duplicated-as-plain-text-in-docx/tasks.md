# Tasks

- [x] Task 1: MergedBlock 增加 `is_formula` 自动检测属性
  - [x] SubTask 1.1: 在 `__init__` 中检查 `original_blocks` 是否有 `is_formula=True` 的块，设置 `self.is_formula`
  - [x] SubTask 1.2: 更新 `to_dict()` 方法包含 `is_formula` 字段

- [x] Task 2: DOCX 端 — 移除 `_add_merged_text` 中公式文本的重复输出
  - [x] SubTask 2.1: 在确定 `text_to_write` 后，遍历 `original_blocks` 移除公式块对应的 LaTeX 文本
  - [x] SubTask 2.2: 清理移除后多余空白，移除后为空时跳过写入

- [x] Task 3: MD 端 — 修复公式包裹逻辑使其对 MergedBlock 生效
  - [x] SubTask 3.1: `_process_page_elements` 中利用 `block.is_formula`（MergedBlock 新属性）判断公式
  - [x] SubTask 3.2: `_insert_element_in_merged_block` 中同样利用新属性判断
  - [x] SubTask 3.3: 公式块宽度 bbox 计算优先使用 `max_width` (MergedBlock)，兼容旧 `block_bbox` 路径

- [x] Task 4: 验证
  - [x] SubTask 4.1: 语法检查通过（`python -m py_compile` 退出码 0）
  - [x] SubTask 4.2: 运行现有测试，4 passed
  - [ ] SubTask 4.3: 人工验证：翻译包含公式的 PDF，检查 DOCX 中公式 LaTeX 不再重复 / MD 中公式正确被 `$`/`$$` 包裹

# Task Dependencies

- [Task 2], [Task 3] 均依赖 [Task 1]
