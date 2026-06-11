# Tasks

- [x] Task 1: 修复 set_result 和 cancel 根据 task_type 显示正确消息
  - [x] SubTask 1.1: 修改 `models/task.py` 中 `set_result` 方法，glossary 任务显示"术语提取完成！"
  - [x] SubTask 1.2: 修改 `models/task.py` 中 `cancel` 方法，glossary 任务显示"术语提取已取消"和"用户取消了术语提取任务"

- [x] Task 2: 修复 process_translation_sync 中 progress_callback 与 PHASE_CONFIG 对齐
  - [x] SubTask 2.1: 将 `process_translation_sync` 中所有 `progress_callback(硬编码百分比, 消息)` 替换为 `progress_callback(task.progress, task.message)`
  - [x] SubTask 2.2: 移除所有手动编写的 progress_callback 调用（共约 8 处），改为在 `update_phase_progress` 后自动调用

- [x] Task 3: 修复 app.py 中 glossary 错误处理
  - [x] SubTask 3.1: 将 `app.py` 中 glossary 路由的 `task.set_status('error'); task.error = str(e)` 替换为 `task.set_error(f"术语提取失败: {str(e)}")`

- [x] Task 4: 修复 clean 阶段消息
  - [x] SubTask 4.1: 将 `_complete_task` 中 `clean` 100% 的消息从"翻译完成！"改为"临时文件清理完成"

- [x] Task 5: 修复进度倒退问题
  - [x] SubTask 5.1: 移除 `_create_translators` 中的 `task.update_phase_progress('translation', 0, '正在创建翻译器...')` 调用
  - [x] SubTask 5.2: 移除 `_translate_content` 中的 `task.update_phase_progress('translation', 5, '准备开始翻译文本内容...')` 调用
  - [x] SubTask 5.3: 修改 `translate_content` 中 semantic_merge=False 时的逻辑，不设置 semantic_merge 100%，直接进入 translation 阶段

- [x] Task 6: 修复 init 阶段重复设置
  - [x] SubTask 6.1: 移除 `process_translation` 中的 init 0%/50%/100% 更新（3 行），因为 app.py 已设置
  - [x] SubTask 6.2: 移除 `process_translation_sync` 中的 init 0%/50%/100% 更新（3 行），因为 CLI 已设置

- [x] Task 7: 修复 glossary 服务进度消息
  - [x] SubTask 7.1: 移除 `extract_glossary_from_pdf` 中重复的 init 100% 设置
  - [x] SubTask 7.2: 在 `extract_glossary_from_pdf` 中 pdf_extraction 100% 之前添加 0% 起始更新
  - [x] SubTask 7.3: 移除 `extract_glossary_sync` 中重复的 init 100% 设置
  - [x] SubTask 7.4: 在 `extract_glossary_sync` 中 pdf_extraction 100% 之前添加 0% 起始更新
  - [x] SubTask 7.5: 将 `extract_glossary_sync` 中 progress_callback 硬编码百分比替换为从 task.progress 读取

# Task Dependencies
- Task 1 独立，可先行
- Task 2 独立
- Task 3 独立
- Task 4 独立
- Task 5 依赖 Task 6（init 不重复后，进度流才清晰）
- Task 6 独立
- Task 7 独立
- Task 1-4, 6, 7 可并行
