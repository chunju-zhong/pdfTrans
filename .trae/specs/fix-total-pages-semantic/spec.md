# 修复翻译进度显示混淆页数与块数 Spec

## Why
翻译进度显示"正在翻译文本: 225/242"，用户将 242 误解为"总页数"，实际 242 是文本块数量。用户选择翻译 20-60 页（41 页），看到 242 会困惑。进度消息应明确区分"文本块"和"页"。

## What Changes
- 将翻译进度消息从"正在翻译文本: X/Y"改为"正在翻译文本块: X/Y"或"正在翻译: X/Y 个文本块"，明确单位
- 检查所有进度消息，确保"页"和"块"单位清晰

## Impact
- Affected code: `services/translation_service.py`

## ADDED Requirements

无

## MODIFIED Requirements

### Requirement: 翻译进度消息明确单位
翻译进度消息 SHALL 明确使用"文本块"而非模糊的"文本"，避免与"页"混淆。

#### Scenario: 翻译进度显示
- **WHEN** 翻译进度更新为 225/242 个文本块
- **THEN** 消息显示"正在翻译: 225/242 个文本块"或类似明确单位

## REMOVED Requirements

无
