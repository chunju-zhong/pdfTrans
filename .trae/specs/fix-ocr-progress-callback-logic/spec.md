# 修复 OCR 进度回调逻辑 Spec

## Why
`_ocr_progress_cb` 中 `STEP_WEIGHTS = {1: 0.45, 1.5: 0.05, 2: 0.25, 3: 0.25}`，但当前 `extract_from_pdf` 只有两个步骤：步骤 1（版面分析+文本OCR+公式+表格，发送回调）和步骤 2（图像裁剪，不发送回调）。步骤 1.5 和步骤 3 不存在。这导致 OCR 进度在步骤 1 完成后永远卡在 45%，剩余 55% 的进度永远不会推进。步骤 2（图像裁剪）虽然存在但不发送回调，其 25% 权重也无法消耗。

## What Changes
- 调整 `STEP_WEIGHTS` 为：步骤 1 = 0.80，步骤 2 = 0.20（移除不存在的步骤 1.5 和步骤 3）
- 在 `extract_from_pdf` 中为步骤 2 添加 `step_start`/`step_complete` 回调
- 在 `_ocr_progress_cb` 中处理 `step_complete` 时将进度推进到当前步骤的累积权重上限
- 移除步骤 1.5 的跳过警告处理（公式识别已合并到步骤 1，不存在单独跳过的情况）
- 保留 `batch_idx`/`total_batches` 处理（`pdf_extractor.py` 批处理路径会发送这些字段）

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`、`services/translation_service.py`
- Affected specs: add-ocr-progress-feedback、optimize-extraction-progress

## ADDED Requirements

### Requirement: STEP_WEIGHTS 反映实际步骤
`STEP_WEIGHTS` SHALL 只包含实际存在的步骤。

当前 `extract_from_pdf` 的步骤结构：
- 步骤 1：版面分析+文本OCR+公式识别+表格识别（最耗时，约 80%）
- 步骤 2：图表/印章图像裁剪（较轻量，约 20%）

新 `STEP_WEIGHTS`：`{1: 0.80, 2: 0.20}`

#### Scenario: 步骤 1 完成后进度到 80%
- **WHEN** 步骤 1 完成，收到 step_complete
- **THEN** OCR 进度推进到 80%

#### Scenario: 步骤 2 完成后进度到 100%
- **WHEN** 步骤 2 完成，收到 step_complete
- **THEN** OCR 进度推进到 100%

### Requirement: 步骤 2 发送进度回调
`extract_from_pdf` SHALL 在步骤 2（图像裁剪）开始和完成时发送 `step_start` 和 `step_complete` 回调。

#### Scenario: 图像裁剪步骤开始
- **WHEN** 开始裁剪图表/印章图像
- **THEN** 发送 `step_start` 回调，step=2，step_name='图像裁剪'

#### Scenario: 图像裁剪步骤完成
- **WHEN** 图像裁剪完成
- **THEN** 发送 `step_complete` 回调，step=2，step_name='图像裁剪'

### Requirement: step_complete 推进进度到步骤权重上限
`_ocr_progress_cb` SHALL 在收到 `step_complete` 时将进度推进到当前步骤的累积权重上限，而非停留在最后一个 `step_progress` 的位置。

#### Scenario: 步骤 1 完成
- **WHEN** 步骤 1（权重 0.80）完成，收到 step_complete
- **THEN** ocr_progress 设为 0.80，而非停留在步骤 1 最后一个 step_progress 的位置

#### Scenario: 步骤 2 完成
- **WHEN** 步骤 2（权重 0.20）完成，收到 step_complete
- **THEN** ocr_progress 设为 1.00

## MODIFIED Requirements

### Requirement: 移除步骤 1.5 跳过警告处理
`_ocr_progress_cb` 中步骤 1.5 的跳过警告处理 SHALL 被移除，因为公式识别已合并到步骤 1 中，不存在单独跳过步骤 1.5 的情况。

### Requirement: 保留 batch_idx/total_batches 处理
`batch_idx`/`total_batches` 处理 SHALL 保留，因为 `pdf_extractor.py` 的批处理路径通过 `_make_batch_callback` 会发送这些字段。
