# Tasks

- [x] Task 1: 恢复 `_build_text_from_textlines` 的 `is_title` 区分换行清理
  - [x] SubTask 1.1: 在 [modules/ocr/paddle_extractor.py](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py) 的 `_build_text_from_textlines` 方法中，恢复 `is_title` 参数的作用：将 docstring 中"保留参数（不再使用）"改为说明该参数控制是否清理换行符
  - [x] SubTask 1.2: 修改换行清理逻辑（line 616-621）：仅当 `is_title=True` 时执行 `result.replace('\n', ' ')`；`is_title=False` 时保留 `result` 的 `\n` 不变
  - [x] SubTask 1.3: 确认调用处 [paddle_extractor.py:805](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py) 与 [paddle_extractor.py:950](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py) 已传 `is_title=(label in self.TITLE_LABELS)`，无需改动
  - [x] SubTask 1.4: 调整日志：仅在 `is_title=True` 实际清理换行时记录 `[换行符清理]` 日志，避免对保留换行的正文产生噪音日志

- [x] Task 2: 修改 `pdf_extractor` 换行清理为按类型区分
  - [x] SubTask 2.1: 在 [modules/pdf_extractor.py](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py) 的换行清理逻辑（line 454-456）前，确认 `block_type` 的取值与标题判断方式
  - [x] SubTask 2.2: 将无条件 `text_block.block_text.replace('\n', ' ')` 改为仅对标题类 `block_type` 清理换行，非标题类保留 `\n`
  - [x] SubTask 2.3: 若 `pdf_extractor` 无标题类型判断，按现有 `block_type` 取值或文本特征区分（与 paddle_extractor 的 TITLE_LABELS 语义对齐）

- [x] Task 3: 验证修复不破坏现有行为
  - [x] SubTask 3.1: 运行提取相关测试（`tests/` 下 paddle_extractor / pdf_extractor / text_processing 测试），确认全部通过
  - [x] SubTask 3.2: 确认标题类文本仍清理换行（保持单行），不回退 `restore-newline-cleanup-in-text-extraction` 修复的标题渲染问题
  - [x] SubTask 3.3: 检查是否有测试断言"正文/所有文本块无换行符"，若有需同步更新为"仅标题类无换行符"

# Task Dependencies
- Task 3 依赖 Task 1、Task 2 完成
- Task 1 与 Task 2 相互独立，可并行
