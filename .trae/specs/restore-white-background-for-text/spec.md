# 恢复文本和表格文字白底 Spec

## Why
之前将文本框和表格单元格的 redaction 背景从白色改为透明（`fill=None`），但透明背景导致翻译文字与原文重叠时无法有效遮盖原文，影响可读性。当前提取原文文字颜色的方法尚未成熟，暂时恢复白底以保证输出质量，待后续找到可靠的文字颜色提取方法后再优化。

## What Changes
- 将文本块的 redaction 填充色从透明 `None` 恢复为白色 `(1, 1, 1)`
- 将表格单元格的 redaction 填充色从透明 `None` 恢复为白色 `(1, 1, 1)`

## Impact
- Affected code: `modules/pdf_generator.py` 中两处 `add_redact_annot` 调用
  - 第516行：文本块 redaction（`fill=None` → `fill=(1, 1, 1)`）
  - 第1083行：表格单元格 redaction（`fill=None` → `fill=(1, 1, 1)`）
- Affected specs: `fix-textbox-transparent-background`（本次变更回退该 spec 的效果）

## MODIFIED Requirements

### Requirement: 文本框和表格单元格使用白色背景覆盖原文
系统在覆盖原文区域时，SHALL 使用白色背景填充 redaction 区域，以有效遮盖原文并确保翻译文字的可读性。

#### Scenario: 文本块覆盖
- **WHEN** 系统对文本块区域执行 redaction 以删除原文
- **THEN** redaction 区域填充白色 `(1, 1, 1)`，遮盖原文后写入翻译文字

#### Scenario: 表格单元格覆盖
- **WHEN** 系统对表格单元格区域执行 redaction 以删除原文
- **THEN** redaction 区域填充白色 `(1, 1, 1)`，遮盖原文后写入翻译文字

## REMOVED Requirements

### Requirement: 透明背景文本框
**Reason**: 透明背景无法有效遮盖原文，导致翻译文字与原文重叠，可读性差。待后续找到可靠的文字颜色提取方法后再优化为匹配原文背景色。
**Migration**: 暂时使用白色背景，后续优化方向为提取原文文字颜色并使用匹配的背景色。
