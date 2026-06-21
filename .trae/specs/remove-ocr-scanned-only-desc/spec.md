# 移除 OCR 仅限扫描版 PDF 的描述 Spec

## Why
OCR 提取功能并不只适用于扫描版 PDF，也可用于普通 PDF 的版面分析、公式识别、表格提取等场景。当前前端和文档中多处将 OCR 描述为"仅用于扫描版 PDF"，误导用户以为 OCR 只能处理扫描版文档。

## What Changes
- 修改 `templates/index.html` 中 OCR 复选框标签和提示文字，移除"扫描版PDF"限定
- 修改 `README.md` 中所有将 OCR 限定为"scanned PDFs"的描述
- 修改 `README.zh.md` 中所有将 OCR 限定为"扫描版PDF"的描述
- 修改 `SKILL.md` 中 OCR 相关描述

## Impact
- Affected code: `templates/index.html`, `README.md`, `README.zh.md`, `SKILL.md`
- 不涉及功能代码变更，仅文案调整

## ADDED Requirements

### Requirement: OCR 描述应反映通用能力
系统在所有用户可见的文案中，SHALL 将 OCR 描述为通用的 PDF 提取增强功能（版面分析、文字识别、公式识别、表格提取），而非仅限扫描版 PDF。

#### Scenario: 前端 OCR 选项
- **WHEN** 用户查看 Web 界面的 OCR 复选框
- **THEN** 标签和提示文字不包含"扫描版PDF"或"scanned PDF"的限定，而是描述 OCR 的通用能力

#### Scenario: README 文档
- **WHEN** 用户阅读 README 中的 OCR 相关说明
- **THEN** OCR 被描述为可增强 PDF 提取效果的功能，适用于各类 PDF，而非仅限扫描版

#### Scenario: SKILL.md 文档
- **WHEN** 用户阅读 SKILL.md 中的 OCR 模式说明
- **THEN** OCR 模式说明不限定为仅处理扫描版 PDF
