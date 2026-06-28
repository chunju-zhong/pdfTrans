# Tasks

- [x] Task 1: 在 `_ocr_progress_cb` 中增加 `page_error` 消息分支
  - [x] SubTask 1.1: 在 `services/translation_extractor.py` 的 `_ocr_progress_cb` 函数开头增加 `if msg_type == 'page_error':` 分支
  - [x] SubTask 1.2: 分支内调用 `task.add_warning(f"第 {payload['page_num']} 页 OCR 提取失败: {payload['error']}", context={"process": "extraction", "page": payload['page_num'], "error": payload['error']})`
  - [x] SubTask 1.3: 分支末尾 `return`，避免走到 `else` 分支被当作 `step_progress`
  - [x] SubTask 1.4: 确保 `step_start`/`step_complete`/其他（`step_progress`）分支行为不变

- [x] Task 2: 验证修复效果
  - [x] SubTask 2.1: 运行 `tests/test_llm_ocr.py` 确认无回归（113 通过，6 历史失败与本次改动无关）
  - [x] SubTask 2.2: 运行 `tests/test_semantic_analyzer.py` 确认无回归（11 通过）
  - [x] SubTask 2.3: 验证 `page_error` 消息时 `task.add_warning` 被调用（4 个 mock 测试全部通过）

# Task Dependencies
- Task 2 依赖 Task 1

# 验证结果摘要
- `tests/test_llm_ocr.py` + `tests/test_semantic_analyzer.py`：113 通过，6 历史失败（`TestLlmOcrConfigDefaults::test_llm_ocr_config_defaults`、`TestMixedFormulaTextRendering` 5 个，均为 PDF 生成器 LaTeX 检测的历史问题）
- Mock 验证：4 个测试用例全部通过（page_error 触发 add_warning、step_start/step_progress 不变、多页连续失败触发多次）
- 修改范围：仅 `services/translation_extractor.py` 的 `_ocr_progress_cb` 函数新增 `page_error` 分支，其他逻辑零改动
