# 文本框背景透明化 Spec

## Why
PDF生成时，文本框和表格单元格使用 `add_redact_annot(..., fill=(1, 1, 1))` 填充白色背景来覆盖原文。这导致翻译后的文本区域出现白色方块，遮盖了原始PDF中的背景色、图案或其他视觉元素，影响输出质量。

## What Changes
- 将文本框的 redaction 填充色从白色 `(1, 1, 1)` 改为透明 `None`（PyMuPDF 中 `fill=None` 表示不填充背景色）
- 将表格单元格的 redaction 填充色从白色 `(1, 1, 1)` 改为透明 `None`

## Impact
- Affected code: `modules/pdf_generator.py` 中两处 `add_redact_annot` 调用
  - 第497行：文本块 redaction（`fill=(1, 1, 1)` → `fill=None`）
  - 第1064行：表格单元格 redaction（`fill=(1, 1, 1)` → `fill=None`）

## ADDED Requirements

### Requirement: 透明背景文本框
系统在覆盖原文区域时，SHALL NOT 填充白色背景，而是使用透明背景，以保留原始PDF的视觉元素。

#### Scenario: 文本块覆盖
- **WHEN** 系统对文本块区域执行 redaction 以删除原文
- **THEN** redaction 区域不填充任何颜色（透明），仅删除文字内容

#### Scenario: 表格单元格覆盖
- **WHEN** 系统对表格单元格区域执行 redaction 以删除原文
- **THEN** redaction 区域不填充任何颜色（透明），仅删除文字内容

#### Scenario: 保留原始背景
- **WHEN** 原始PDF页面包含非白色背景（如彩色背景、水印、图案）
- **THEN** 翻译后的文本区域不会出现白色方块，原始背景元素得以保留
