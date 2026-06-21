# 修复 LLM OCR 提取进度条不更新 Spec

## Why
LLM OCR 模式提取 PDF 时，进度条停留在 0% 不更新，用户无法感知处理进度。PaddleOCR 路径已实现 `progress_callback` 机制，但 LLM OCR 路径完全缺失。

## What Changes
- `LlmOcrExtractor.extract_from_pdf` 新增 `progress_callback` 参数
- 逐页处理循环中，每完成一页调用回调更新进度
- `PdfExtractor.extract` 中 LLM OCR 分支传递 `progress_callback` 给 `extract_from_pdf`

## Impact
- Affected code: [llm_extractor.py](modules/ocr/llm_extractor.py) `extract_from_pdf` 方法
- Affected code: [pdf_extractor.py](modules/pdf_extractor.py) `extract` 方法 LLM OCR 分支
- Affected specs: add-ocr-progress-feedback

## ADDED Requirements

### Requirement: LLM OCR 提取进度回调
LLM OCR 提取过程 SHALL 通过 progress_callback 报告进度。

#### Scenario: 逐页提取进度
- **WHEN** LLM OCR 开始提取 PDF
- **THEN** 每完成一页后调用 `progress_callback('step_progress', payload)` 更新进度
- **AND** payload 包含 `pages_done`（已完成页数）、`total_pages`（总页数）、`step`（步骤编号）、`step_name`（步骤名称）

#### Scenario: 提取开始和完成
- **WHEN** LLM OCR 开始提取
- **THEN** 调用 `progress_callback('step_start', payload)` 标记步骤开始
- **WHEN** 所有页面提取完成
- **THEN** 调用 `progress_callback('step_complete', payload)` 标记步骤完成

### Requirement: PdfExtractor 传递 progress_callback 给 LLM OCR
`PdfExtractor.extract` 的 LLM OCR 分支 SHALL 将 `progress_callback` 传递给 `extract_from_pdf`。

#### Scenario: OCR 模式使用 LLM 引擎
- **WHEN** `ocr_mode=True` 且 `ocr_engine='llm'`
- **THEN** `progress_callback` 被传递给 `extractor.extract_from_pdf()`
