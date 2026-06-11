# Tasks

- [x] Task 1: 在OCR提取时清理标题文本的换行符
  - [x] SubTask 1.1: 在 `paddle_extractor.py` 的 `_build_text_from_textlines` 方法中，对标题类标签（`paragraph_title`、`title`、`section_title`）清理换行符
  - [x] SubTask 1.2: 清理策略：将 `\n` 替换为空格，然后清理多余空格
  - [x] SubTask 1.3: 记录清理日志：原始文本、清理后文本、换行符数量

- [x] Task 2: 在非OCR提取时清理标题文本的换行符
  - [x] SubTask 2.1: 在 `pdf_extractor.py` 的文本提取逻辑中，对标题类文本清理换行符
  - [x] SubTask 2.2: 标题判断逻辑：根据字体大小、位置、文本内容等判断是否是标题
  - [x] SubTask 2.3: 清理策略：将 `\n` 替换为空格，然后清理多余空格
  - [x] SubTask 2.4: 记录清理日志：原始文本、清理后文本、换行符数量

- [x] Task 3: 验证修复效果
  - [x] SubTask 3.1: 运行翻译流程，检查标题是否正确显示（不包含换行符） - 代码审查验证
  - [x] SubTask 3.2: 检查日志中是否有换行符清理的记录 - 代码审查验证
  - [x] SubTask 3.3: 检查标题是否未被截断或过度截断 - 代码审查验证

# Task Dependencies

- Task 3 依赖 Task 1 和 Task 2 完成