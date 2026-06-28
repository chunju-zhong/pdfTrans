# Checklist

## _ocr_progress_cb 修改
- [x] `services/translation_extractor.py` `_ocr_progress_cb` 增加 `if msg_type == 'page_error':` 分支
- [x] 分支内调用 `task.add_warning(f"第 {payload['page_num']} 页 OCR 提取失败: {payload['error']}", context={"process": "extraction", "page": payload['page_num'], "error": payload['error']})`
- [x] 分支末尾 `return`，避免走到 `else` 分支
- [x] `step_start` 分支行为不变
- [x] `step_complete` 分支行为不变
- [x] 其他消息类型（`step_progress`）行为不变

## 不变项验证
- [x] `modules/ocr/llm_extractor.py` 的 `progress_callback('page_error', ...)` 调用方未修改
- [x] `task.add_warning` 机制未修改
- [x] 现有「失败页添加空页面，继续后续页」的降级行为不变
- [x] `task.update_phase_progress` 的进度更新不受影响

## 测试验证
- [x] `tests/test_llm_ocr.py` 现有测试通过（113 通过，6 历史失败与本次改动无关）
- [x] `tests/test_semantic_analyzer.py` 11 个测试全部通过
- [x] `page_error` 消息时 `task.add_warning` 被调用（4 个 mock 测试全部通过）
- [x] 多页连续失败时，每页都调用一次 `task.add_warning`（Test 4 验证通过）
