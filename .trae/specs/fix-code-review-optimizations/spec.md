# Code Review 优化建议 Spec

## Why

Code Review 发现了3个 MEDIUM 和2个 LOW 级别的代码质量问题，需要优化以提升代码可维护性和日志一致性。

## What Changes

- 提取补充捕获中的文本过滤逻辑为独立函数，降低嵌套层级（5层→3层）
- 为 `else`（未知标签）分支添加 `[TEXT_SKIP]` WARNING 日志，与 TEXT_LABELS 分支保持一致
- 将 `SHORT_TEXT_THRESHOLD` 从局部变量提升为模块级常量
- 将 `rec_texts` 长度不匹配 WARNING 日志的标签从 `[FONT_DEBUG]` 改为 `[OCR_WARN]`
- 补充测试注释引用 spec 需求

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`, `modules/extractors/text_analyzer.py`, `tests/test_ocr_extractor.py`

## ADDED Requirements

### Requirement: 补充捕获文本过滤逻辑提取为独立函数

系统 SHALL 将补充捕获中的文本过滤和空列表处理逻辑提取为 `_filter_uncovered_textlines` 静态方法，降低 `_process_page_layout` 的嵌套层级。

#### Scenario: textline_texts 可用

- **WHEN** `textline_texts` 非空且有未覆盖的 textline
- **THEN** 返回有文本的 textline 列表

#### Scenario: textline_texts 不可用

- **WHEN** `textline_texts` 为空但有未覆盖的 textline
- **THEN** 记录 INFO 日志说明无可用的文本数据，返回空列表

### Requirement: else 分支添加 TEXT_SKIP 日志

系统 SHALL 在 `else`（未知标签）分支中，当 `text.strip()` 为空时记录 `[TEXT_SKIP]` WARNING 日志，与 TEXT_LABELS 分支行为一致。

#### Scenario: 未知标签文本提取失败

- **WHEN** 未知标签的文本块 textline 匹配失败且 content 为空
- **THEN** 记录 `[TEXT_SKIP]` WARNING 日志，包含 label、textline_match 和 content 状态

### Requirement: SHORT_TEXT_THRESHOLD 提升为模块级常量

系统 SHALL 将 `SHORT_TEXT_THRESHOLD = 20` 从 `_add_similar_blocks` 函数内部提升为 `text_analyzer.py` 模块级常量。

### Requirement: rec_texts 长度不匹配日志标签修正

系统 SHALL 将 `rec_texts` 长度不匹配 WARNING 日志的标签从 `[FONT_DEBUG]` 改为 `[OCR_WARN]`，准确反映日志性质。

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
