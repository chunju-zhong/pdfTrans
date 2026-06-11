# 修复 OCR 进度消息缺失和倒退 Spec

## Why
`_ocr_progress_cb` 有三个问题：1) `step_progress` 回调的 payload 不包含 `step_name`，导致消息变成"OCR提取:  X/Y页"（缺少步骤名，多一个空格）；2) 进度会倒退到 5%（extraction 阶段起始值），根因是 OCR 重试或分批处理时步骤 1 的 `step_start` 重新发送 `pages_done=0`，导致 `phase_percent=0`，`overall=5%`；3) `message = payload.get('message')` 是死代码，没有任何 OCR 代码发送 `message` 字段。

## What Changes
- 在 `step_progress` 的 payload 中添加 `step_name` 字段（必须包含，不做兼容性兜底）
- 步骤 2 的 `step_start` 不发送 `total_pages`（步骤 2 不按页处理）
- `step_start` 时进度使用前面步骤的累积权重（根因修复，避免 phase_percent=0 导致倒退）
- 移除 `message` 死代码及其消息格式化分支
- 统一消息格式

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`、`services/translation_service.py`

## ADDED Requirements

### Requirement: 所有回调 payload 必须包含 step_name
`step_start`、`step_progress`、`step_complete` 回调的 payload SHALL 都包含 `step_name` 字段。

#### Scenario: step_progress 消息显示步骤名
- **WHEN** 步骤 1 处理到第 3/10 页
- **THEN** 消息显示"OCR提取: 版面分析+文本+公式+表格 3/10页"，而非"OCR提取:  3/10页"

### Requirement: step_start 时进度不倒退
`step_start` 时 SHALL 使用前面所有步骤的累积权重作为进度，而非从 0 开始计算。这避免了 OCR 重试或分批处理时进度倒退到 5%。

#### Scenario: 步骤 2 开始时不倒退
- **WHEN** 步骤 1 完成（进度 80%），步骤 2 开始
- **THEN** 进度保持 80%，不倒退到 5%

#### Scenario: OCR 重试时不倒退
- **WHEN** OCR 失败重试，步骤 1 的 step_start 重新发送
- **THEN** 进度不低于重试前的值

### Requirement: 步骤 2 不发送 total_pages
步骤 2（图像裁剪）不按页处理，`step_start` 回调 SHALL 不包含 `total_pages` 字段。

#### Scenario: 步骤 2 开始消息
- **WHEN** 步骤 2 开始
- **THEN** 消息显示"OCR提取: 图像裁剪开始"，而非"OCR提取: 图像裁剪 0/N页"

### Requirement: 消息格式统一
`_ocr_progress_cb` 的消息格式 SHALL 统一为：
- `step_start`: "OCR提取: {step_name}开始"
- `step_progress`: "OCR提取: {step_name} {pages_done}/{total_pages}页"
- `step_complete`: "OCR提取: {step_name}完成"

## MODIFIED Requirements

### Requirement: step_progress payload 包含 step_name
`paddle_extractor.py` 中 `step_progress` 回调 SHALL 包含 `step_name` 字段。

### Requirement: 步骤 2 step_start 不发送 total_pages
`paddle_extractor.py` 中步骤 2 的 `step_start` 回调 SHALL 不包含 `total_pages` 字段。

## REMOVED Requirements

### Requirement: message 字段处理
**Reason**: 没有任何 OCR 代码发送 `message` 字段，这是死代码。
**Migration**: 移除 `message = payload.get('message')` 和 `if message: msg = f"OCR提取: {message}"` 分支。

### Requirement: step_start 时 pages_done=0 的进度计算
**Reason**: `step_start` 时 `pages_done=0` 导致 `phase_percent=0`，进度倒退到 5%。
**Migration**: `step_start` 时 `phase_percent` 使用前面步骤的累积权重对应的百分比，而非从 0 计算。
