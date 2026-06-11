# 修复 Rect.intersect() 原地修改导致文本块重叠检测失效 Spec

## Why

第22页表格最后一行单元格右侧露出一小段压住的文字，显示了 "...夜》和《向日..." 和 "...毕加索、康定..."。

**根因**：PyMuPDF 的 `Rect.intersect()` **原地修改**调用者矩形（`r1.intersect(r2)` 后 `r1` 被改为交集结果），导致 `_extract_text_blocks` 中遍历多个单元格计算重叠面积时，第一次调用后 `block_rect` 被破坏，后续所有重叠计算全部错误。因此表格内的文本块无法被正确识别为表格文本，同时作为文本块和单元格内容被渲染两次。

此 bug 影响所有使用 `Rect.intersect()` 在循环中计算重叠面积的代码路径。

## What Changes

- 将所有 `.intersect()` 调用替换为 `&` 运算符（返回新矩形，不修改原矩形）
- 修复文件：`pdf_extractor.py`、`table_processor.py`、`style_analyzer.py`
- 累积重叠面积逻辑和空列表回退逻辑保留
- 表格 bbox 字符过滤逻辑保留
- 移除所有 `[DIAG]` 诊断日志，保留有价值的 debug 日志

## Impact

- Affected code: `modules/pdf_extractor.py`、`modules/extractors/table_processor.py`、`modules/extractors/style_analyzer.py`

## ADDED Requirements

### Requirement: 使用 & 运算符计算矩形交集

在所有需要计算矩形交集的场景中，SHALL 使用 `&` 运算符（`rect1 & rect2`）而非 `rect1.intersect(rect2)`，因为 `intersect()` 会原地修改调用者矩形。

#### Scenario: 循环中计算多个矩形交集

- **WHEN** 在循环中对同一矩形与多个其他矩形计算交集
- **THEN** SHALL 使用 `&` 运算符确保原始矩形不被修改
- **AND** 每次交集计算 SHALL 基于原始矩形

## MODIFIED Requirements

无

## REMOVED Requirements

无
