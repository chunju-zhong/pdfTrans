# 修复 paragraph_title 标签处理 Spec

## Why

`paragraph_title` 是 PP-DocLayout-V3 模型返回的有效布局标签（如 "Oxygen transfer efficiency"），但不在 `TEXT_LABELS` 中，导致它通过 unknown label 警告后仅以 fallback 方式处理，缺少字体大小估算等关键逻辑。

## What Changes

- **添加 `paragraph_title` 到 `TEXT_LABELS`**：确保标题类标签得到完整的文本块处理
- **验证 `vision_footnote` 处理**：确保其他 PP-DocLayout-V3 特有标签也有正确处理

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`
- 行为变更：`paragraph_title` 标签获得完整的文本块处理（字体估算、body 判断等）

## ADDED Requirements

### Requirement: paragraph_title 标签映射

系统 SHALL 将 `paragraph_title` 视为标题类文本标签，与 `title` 标签同等处理。

#### Scenario: paragraph_title 文本块创建

- **WHEN** 布局分析返回 `label='paragraph_title'`
- **THEN** 将其归类为 `TEXT_LABELS`，执行完整的文本块创建逻辑（字体估算、bbox 验证等）
- **AND** 标记 `is_body_text=False`（与 `title` 一致）

## MODIFIED Requirements

### Requirement: TEXT_LABELS 集合

`TEXT_LABELS` SHALL 包含 `paragraph_title`。

## REMOVED Requirements

（无移除的需求）
