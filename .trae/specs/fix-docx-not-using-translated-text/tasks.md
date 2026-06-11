# Tasks

- [x] Task 1: 修改 `_add_merged_text` 使用翻译文本 + 重命名易误解变量
  - [x] SubTask 1.1: 将 `docx_generator.py` 第691行 `text_block.block_text` 改为 `translated_item.block_text`（保留 fallback 逻辑）
  - [x] SubTask 1.2: 将 `_add_merged_text` 参数 `merged_item` 重命名为 `translated_item`，更新方法体内所有引用
  - [x] SubTask 1.3: 更新 `_add_paragraph_elements` 中调用 `_add_merged_text` 处的局部变量名（无需修改：`block`、`before_block`、`after_block` 本身具描述性）
  - [x] SubTask 1.4: 验证公式块处理不受影响（第688-690行行为不变，仅通用文本路径修改）
  - [x] SubTask 1.5: 运行 Python 语法检查通过，21/21 测试通过

- [ ] Task 2: 运行程序验证修复效果（需要包含文本的 PDF 端到端运行）
  - [ ] SubTask 2.1: 运行 `output_format=all` 生成 PDF 和 DOCX
  - [ ] SubTask 2.2: 检查生成的 DOCX 文件内容是否为中文翻译而非英文原文
  - [ ] SubTask 2.3: 检查生成的 PDF 与 DOCX 内容一致

# Task Dependencies

- Task 2 依赖 Task 1
