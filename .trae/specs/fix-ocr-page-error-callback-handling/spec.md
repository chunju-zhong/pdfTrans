# OCR page_error 回调处理缺失修复 Spec

## Why

`modules/ocr/llm_extractor.py:261` 在单页 OCR 失败时调用 `progress_callback('page_error', {'page_num':..., 'error':...})`，
但接收方 [services/translation_extractor.py:86-110](file:///Users/chunju/work/pdfTrans/services/translation_extractor.py#L86) 的 `_ocr_progress_cb` 回调
**只处理 `step_start`/`step_complete`/其他（当作 `step_progress`）三种消息类型**，未处理 `page_error`。

结果：`page_error` 走到 `else` 分支被当作普通进度更新，`error` 字段被完全丢弃，
从未调用 `task.add_warning(...)` 或 `task.set_error(...)`，UI 完全收不到具体错误原因。

日志中可见 `第7页LLM OCR提取错误: LLM OCR API 请求失败: max_tokens 参数超限...`，
但 UI 上无任何提示，用户只能看到进度条持续推进，以为系统正常工作。

## What Changes

- `services/translation_extractor.py` `_ocr_progress_cb` 增加 `page_error` 消息分支：
  - 调用 `task.add_warning(f"第 {page_num} 页 OCR 提取失败: {error}", context={"process": "extraction", "page": page_num, "error": error})`
  - 不中断流程（保持现有「失败页添加空页面，继续后续页」的行为）

## Impact

- Affected specs:
  - `fix-llm-api-error-reporting-to-ui` — 其检查清单声称「错误仍通过 `progress_callback('page_error', ...)` 上报（机制未修改）」，
    但实际接收方未处理该消息，本 spec 修复接收方
  - `fix-llm-ocr-error-propagation` — 该 spec 让 `_extract_page` 返回错误字符串并通过 `page_error` 回调传播，
    本 spec 完成最后一公里：让回调接收方真正处理该消息
  - `fix-llm-ocr-timeout-error-message` — 超时错误也通过 `page_error` 传播，本 spec 使其也能到达 UI
- Affected code:
  - `services/translation_extractor.py` — `_ocr_progress_cb` 增加 `page_error` 分支

## ADDED Requirements

### Requirement: OCR page_error 回调处理

系统 SHALL 在 `services/translation_extractor.py` 的 `_ocr_progress_cb` 回调中处理 `page_error` 消息类型，
将单页 OCR 失败的具体原因通过 `task.add_warning(...)` 上报到 UI。

#### Scenario: 单页 OCR 失败（如 max_tokens 超限）

- **WHEN** `progress_callback('page_error', {'page_num': 7, 'error': 'LLM OCR API 请求失败: max_tokens 参数超限...'})` 被调用
- **THEN** `_ocr_progress_cb` SHALL 调用 `task.add_warning(f"第 7 页 OCR 提取失败: LLM OCR API 请求失败: max_tokens 参数超限...", context={"process": "extraction", "page": 7, "error": "LLM OCR API 请求失败: max_tokens 参数超限..."})`
- **AND** 不中断后续页处理（保持现有降级行为）
- **AND** 不覆盖 `step_progress` 的进度更新（`page_error` 分支单独处理，不与进度更新冲突）

#### Scenario: 多页连续失败

- **WHEN** 第 7、8、9 页均触发 `page_error`
- **THEN** 每页都 SHALL 调用一次 `task.add_warning(...)`，UI 收到 3 条警告
- **AND** 任务继续处理后续页

#### Scenario: 正常进度更新不受影响

- **WHEN** `progress_callback('step_start'/'step_progress'/'step_complete', ...)` 被调用
- **THEN** 保持现有行为不变（更新 `task.update_phase_progress`）

## Implementation Notes

- `page_error` 分支应在 `if msg_type == 'step_start'` / `elif msg_type == 'step_complete'` / `else` 之前单独判断，
  避免 `page_error` 走到 `else` 分支被当作 `step_progress`
- `task.add_warning` 的 `context` 字典应包含 `page`（页码）和 `error`（错误消息）字段，
  便于 UI 分类展示
- 不修改 `llm_extractor.py` 的 `progress_callback('page_error', ...)` 调用方
- 不修改 `task.add_warning` 机制本身
- 本 spec 仅修复「最后一公里」：让接收方处理 `page_error` 消息
