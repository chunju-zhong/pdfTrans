# OCR 分批失败静默吞没修复 + 提取完整性保障 Spec

## Why
OCR 分批处理中部分批次失败时，`_merge_batch_results` 静默丢弃失败批次（None），只合并成功的结果。翻译服务不检查提取页数是否与预期一致，也不添加任何警告。前端显示"翻译完成"，用户以为翻译了全部页面，实际只翻译了部分页面。

## What Changes
- `_merge_batch_results` 新增 `all_page_nums` 参数，返回 `(PdfExtraction, list[int])` 元组包含缺失页码
- **BREAKING**: `PdfExtractor.extract` 返回值从 `PdfExtraction` 改为 `(PdfExtraction, list[int])` 元组
- `translation_service.extract_pdf_content` 适配新返回值，缺失页码时调用 `task.add_warning()`
- 非 OCR 路径的单页处理失败也收集到缺失页码列表
- "页面无正文块"警告从仅日志改为同时调用 `task.add_warning()`

## Impact
- Affected specs: ocr-three-layer-protection-and-batching（分批合并逻辑变更）
- Affected code: `modules/pdf_extractor.py`、`services/translation_service.py`

## ADDED Requirements

### Requirement: 分批失败缺失页码追踪
系统 SHALL 在 OCR 分批处理中追踪失败批次的缺失页码，并通过返回值向上层传递。

#### Scenario: 部分批次失败
- **WHEN** 40 页 PDF 分 8 批处理，第 4 批（16-20页）和第 7 批（31-35页）失败
- **THEN** `_merge_batch_results` 返回的缺失页码列表为 [16, 17, 18, 19, 20, 31, 32, 33, 34, 35]

#### Scenario: 全部批次成功
- **WHEN** 所有批次 OCR 成功
- **THEN** 缺失页码列表为空 []

#### Scenario: 全部批次失败
- **WHEN** 所有批次 OCR 失败
- **THEN** 缺失页码列表包含所有目标页码，`PdfExtraction` 为空结果

### Requirement: 提取缺失页码警告
系统 SHALL 在提取结果存在缺失页码时，通过 `task.add_warning()` 通知用户。

#### Scenario: OCR 部分批次失败
- **WHEN** OCR 提取完成后存在缺失页码
- **THEN** 调用 `task.add_warning("OCR提取失败，以下页面内容缺失: [16, 17, ...]", context={"process": "extraction", "missing_pages": [...]})`

#### Scenario: 非 OCR 路径单页处理失败
- **WHEN** PyMuPDF 提取某页失败
- **THEN** 该页码加入缺失页码列表，同样通过 `task.add_warning()` 通知

#### Scenario: 页面无正文块
- **WHEN** 某页提取成功但无正文块
- **THEN** 调用 `task.add_warning("以下页面无正文内容: [5, 12]", context={"process": "extraction"})`

## MODIFIED Requirements

### Requirement: _merge_batch_results 返回缺失页码
`_merge_batch_results` 函数签名新增 `all_page_nums` 参数（所有预期页码列表），返回值从 `PdfExtraction` 改为 `(PdfExtraction, list[int])` 元组。

### Requirement: PdfExtractor.extract 返回缺失页码
`PdfExtractor.extract` 返回值从 `PdfExtraction` 改为 `(PdfExtraction, list[int])` 元组。所有返回路径统一返回元组：OCR 分批路径返回合并结果+缺失页码，OCR 单批路径和非 OCR 路径返回 `(result, [])`。
