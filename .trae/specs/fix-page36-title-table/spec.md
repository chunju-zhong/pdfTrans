# 修复36页标题和表格识别、38页公式和文字识别问题 Spec

## Why

当前存在三个问题：1）`paragraph_title` 等未识别的标签导致标题丢失；2）`_clean_latex` 引用错误 `cls` 导致38页版面分析崩溃，文字丢失；3）公式渲染输出不清晰。

## What Changes

- **添加未知标签的 fallback 处理**：将 `paragraph_title`、`vision_footnote` 等未知标签归类为 text 或 title
- **修复 `_clean_latex` 引用错误**：已在之前修复，此处验证
- **修复 `paragraph_title` 标签映射**

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`
- 行为变更：未知标签不再丢失，而是归类处理

## ADDED Requirements

### Requirement: 未知标签 fallback 处理

系统 SHALL 在遇到未识别的布局标签时，使用 fallback 策略而不是丢弃。

#### Scenario: paragraph_title 标签处理

- **WHEN** 布局分析返回 `label='paragraph_title'`
- **THEN** 将其归类为 `title` 类型的文本块（is_title=True, is_body=False）

#### Scenario: vision_footnote 标签处理

- **WHEN** 布局分析返回 `label='vision_footnote'`
- **THEN** 将其归类为普通 text 文本块

#### Scenario: 其他未知标签处理

- **WHEN** 遇到任何未识别的 label
- **THEN** 归类为普通 text 文本块，记录 WARNING 日志

### Requirement: 表格识别启用

系统 SHALL 在配置 `OCR_SKIP_TABLE=False` 时启用表格识别。

#### Scenario: 表格识别启用

- **WHEN** `OCR_SKIP_TABLE=False`
- **THEN** `use_table=True`，传入 PPStructureV3

## MODIFIED Requirements

### Requirement: 标签映射逻辑

`_process_page_layout` 中的标签处理逻辑 SHALL 包含 `paragraph_title`、`vision_footnote` 等额外标签的处理分支。

## REMOVED Requirements

（无移除的需求）
