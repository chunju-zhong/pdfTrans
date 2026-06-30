# 术语提取 UI 提示：不支持 OCR 识别图片 Spec

## Why
术语提取功能当前仅基于 PDF 内嵌文本层（`PdfExtractor`）进行提取，不会对图片/扫描页做 OCR。用户上传扫描版或图片型 PDF 时，术语提取会得到空结果或残缺结果，且 UI 上没有任何提示，导致用户误以为功能故障。需要在术语提取入口处增加清晰的 UI 提示，说明仅支持 PDF 中的文本，避免误解。

## What Changes
- 在术语提取按钮下方的提示文案中，补充说明"仅支持 PDF 中的文本，不支持 OCR 识别图片中的文字"。
- 仅修改前端模板 `templates/index.html` 中术语提取区域的 `form-hint` 文案，不改动任何后端逻辑、不新增接口、不改动 JS 行为。

## Impact
- Affected specs: 无（纯前端文案调整）
- Affected code: `templates/index.html`（术语提取区块，约第 112 行的 `form-hint`）

## ADDED Requirements
### Requirement: 术语提取 UI 提示需说明不支持 OCR
术语提取入口 SHALL 在 UI 上明确告知用户：术语提取仅基于 PDF 中的文本，不支持通过 OCR 识别图片/扫描页中的文字。

#### Scenario: 用户查看术语提取入口
- **WHEN** 用户在翻译页查看"提取术语"按钮下方提示
- **THEN** 提示文案同时包含原说明（使用当前页码范围从 PDF 提取术语表）以及"仅支持 PDF 中的文本，不支持 OCR 识别图片中的文字"的说明

#### Scenario: 用户上传扫描版 PDF
- **WHEN** 用户上传图片型/扫描版 PDF 并点击"提取术语"
- **THEN** 用户在点击前已能看到不支持 OCR 的提示，无需依赖运行时报错

## MODIFIED Requirements
无

## REMOVED Requirements
无
