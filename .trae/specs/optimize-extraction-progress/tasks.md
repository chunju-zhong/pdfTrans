# Tasks

- [x] Task 1: 重新分配 PHASE_CONFIG 阶段百分比区间
  - [x] SubTask 1.1: 修改 `models/phase_config.py` 中 `PHASE_CONFIG` 的区间：init 0-5, extraction 5-40, semantic_merge 40-50, translation 50-85, table_translation 85-92, generation 92-98, clean 98-100
  - [x] SubTask 1.2: 验证 `validate_phase_config` 仍能正确验证新配置

- [x] Task 2: 修复整数截断问题，使用四舍五入
  - [x] SubTask 2.1: 修改 `models/phase_config.py` 中 `calculate_progress` 函数，将 `(end - start) * phase_percent // 100` 改为 `round((end - start) * phase_percent / 100)`
  - [x] SubTask 2.2: 修改 `models/task.py` 中 `update_phase_progress` 方法，同样使用 `round()` 替代 `//`

- [x] Task 3: 修复 set_error 保留当前进度
  - [x] SubTask 3.1: 修改 `models/task.py` 中 `set_error` 方法，移除 `self.progress = 0`，保留当前进度值

- [x] Task 4: 修复 _complete_task 进度流程
  - [x] SubTask 4.1: 将 `generation` 50% 的进度更新移到 `_generate_outputs` 调用之前
  - [x] SubTask 4.2: 在 `_generate_outputs` 完成后设置 `generation` 100% 并消息为"输出文件生成完成"
  - [x] SubTask 4.3: 清理完成后设置 `clean` 100% 并消息为"翻译完成！"
  - [x] SubTask 4.4: 移除 `_complete_task` 中多余的 generation 阶段更新

- [x] Task 5: 无表格时平滑过渡
  - [x] SubTask 5.1: 修改 `translate_tables` 方法，当 `tables` 为空列表时直接返回空列表，不调用 `update_phase_progress('table_translation', ...)`

- [x] Task 6: 语义合并阶段细粒度进度
  - [x] SubTask 6.1: 修改 `merge_semantic_blocks` 调用，添加进度回调，在合并过程中更新进度
  - [x] SubTask 6.2: 修改 `merge_semantic_blocks_with_llm` 调用，添加进度回调
  - [x] SubTask 6.3: 修改 `merge_semantic_blocks_with_llm_two_phase` 调用，添加进度回调
  - [x] SubTask 6.4: 进度消息格式："正在合并语义块: X/Y"

- [x] Task 7: 生成阶段细粒度进度
  - [x] SubTask 7.1: 在 `generate_output_files` 方法中，根据输出格式数量更新进度
  - [x] SubTask 7.2: 进度消息格式："正在生成输出文件: PDF..." / "正在生成输出文件: DOCX..."

# Task Dependencies
- Task 1 和 Task 2 无依赖，可并行
- Task 3、4、5 互相独立，可并行
- Task 6 依赖 Task 1（新区间生效后才有意义）
- Task 7 依赖 Task 4（修正流程后再添加细粒度）
