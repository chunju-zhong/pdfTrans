# Tasks

- [x] Task 1: 步骤1改回 use_formula=False
  - [x] SubTask 1.1: 确认 `paddle_extractor.py` 步骤1管线创建参数 `use_formula=False`（已确认当前代码已是 False）

- [x] Task 2: 新增步骤1.5纯公式版面分析
  - [x] SubTask 2.1: 在步骤1完成后、步骤2之前，新增步骤1.5代码块
  - [x] SubTask 2.2: 步骤1.5逐页创建 `use_formula=True` 管线，调用 `pipeline.predict()` 检测公式区域
  - [x] SubTask 2.3: 检查 `parsing_res_list` 中是否有 `formula`/`formula_number` 标签，更新 `all_layout_results[p]['has_formula']`
  - [x] SubTask 2.4: 每页处理完后 `del pipeline` + `gc.collect()`（finally 块确保释放）
  - [x] SubTask 2.5: 步骤1.5开始前检查可用内存 < 1.5GB 时跳过并通知用户
  - [x] SubTask 2.6: 添加步骤1.5的进度回调（step_start/step_progress/step_complete）
  - [x] SubTask 2.7: 添加步骤1.5的内存日志

- [x] Task 3: 步骤3使用步骤1.5的检测结果
  - [x] SubTask 3.1: 确认步骤3的 `formula_pages` 筛选逻辑使用 `all_layout_results` 中的 `has_formula`（步骤1.5已更新）

- [x] Task 4: 公式识别被跳过时通知用户
  - [x] SubTask 4.1: 步骤1.5内存不足跳过时通过 status_callback 发送警告消息
  - [x] SubTask 4.2: OCR_SKIP_FORMULA 配置跳过时通过 status_callback 发送提示消息
  - [x] SubTask 4.3: translation_service.py 检测 step_complete skipped 事件，调用 task.add_warning()

- [x] Task 5: 各步骤管线正确释放
  - [x] SubTask 5.1: 步骤1管线释放（del layout_pipeline + gc.collect）
  - [x] SubTask 5.2: 步骤1.5管线释放（finally 块中 del formula_detect_pipeline + gc.collect）
  - [x] SubTask 5.3: 步骤2管线释放改进（pipeline=None 初始化 + finally 块）
  - [x] SubTask 5.4: 步骤3管线释放改进（pipeline=None 初始化 + finally 块）

- [x] Task 6: 更新 translation_service.py 的 STEP_WEIGHTS
  - [x] SubTask 6.1: STEP_WEIGHTS 更新为 {1: 0.45, 1.5: 0.05, 2: 0.25, 3: 0.25}
  - [x] SubTask 6.2: 进度回调支持 message 字段（公式跳过提示）
  - [x] SubTask 6.3: 进度回调检测 step_complete skipped 事件

# Task Dependencies
- Task 1 和 Task 2 已合并执行
- Task 3 依赖 Task 2（步骤1.5更新 has_formula 后步骤3自动生效）✅
- Task 4 和 Task 5 独立于 Task 2-3 ✅
