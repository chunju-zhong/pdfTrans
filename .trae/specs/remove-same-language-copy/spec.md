# 移除源语言=目标语言 PDF 直接拷贝逻辑 Spec

## Why

当源语言=目标语言时，系统直接拷贝原始 PDF 页面（`handle_same_language()`），跳过了整个提取/识别/输出流程。这导致：Word 和 Markdown 输出格式无法生成（用户得到的是 PDF 文件而非 .docx/.md），OCR 模式下无法重建可搜索文本，且表格/公式等结构化内容无法提取和输出。翻译器层已正确处理同语言情况（返回原始文本），因此 `handle_same_language()` 的早期返回是冗余且有害的。

## What Changes

- **移除 `handle_same_language()` 早期返回**：删除 `process_translation()` 和 `process_translation_sync()` 中的 `source_lang == target_lang` 检查和 `handle_same_language()` 调用
- **删除 `handle_same_language()` 方法**：该方法不再被调用
- 同语言时走正常流程：提取→翻译（翻译器返回原始文本）→生成 PDF/Word/MD

## Impact

- Affected code: `services/translation_service.py`
- 行为变更：同语言时不再秒级完成（需要走完整提取+输出流程），但输出格式正确

## ADDED Requirements

### Requirement: 源语言=目标语言时走正常提取和输出流程

系统 SHALL 在源语言=目标语言时走正常的提取→翻译→输出流程，而非直接拷贝 PDF。翻译器已内置同语言处理逻辑（返回原始文本），无需特殊分支。

#### Scenario: 源语言=目标语言，输出 PDF

- **WHEN** 用户上传 PDF，源语言=目标语言，输出格式为 PDF
- **THEN** 系统正常提取文本/表格/图像
- **AND** 翻译器返回原始文本（不调用翻译 API）
- **AND** 生成带覆盖层的 PDF 输出（文本可搜索）

#### Scenario: 源语言=目标语言，输出 Word

- **WHEN** 用户上传 PDF，源语言=目标语言，输出格式为 Word
- **THEN** 系统正常提取文本/表格/图像
- **AND** 翻译器返回原始文本
- **AND** 生成 .docx 文件（而非错误地拷贝 PDF）

#### Scenario: 源语言=目标语言，输出 Markdown

- **WHEN** 用户上传 PDF，源语言=目标语言，输出格式为 Markdown
- **THEN** 系统正常提取文本/表格/图像
- **AND** 翻译器返回原始文本
- **AND** 生成 .md 文件（而非错误地拷贝 PDF）

## MODIFIED Requirements

### Requirement: 源语言=目标语言处理逻辑

从"直接拷贝原始 PDF 页面"改为"走正常提取→翻译→输出流程"。翻译器在同语言时返回原始文本，不消耗 API 额度。

## REMOVED Requirements

### Requirement: handle_same_language() 方法

**Reason**: 该方法跳过整个提取/翻译/输出流程，仅拷贝 PDF，无法生成 Word/Markdown 输出，且与翻译器内置的同语言处理逻辑冗余。
**Migration**: 删除该方法及其所有调用点。同语言场景由翻译器层自动处理。
