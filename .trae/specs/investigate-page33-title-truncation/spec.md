# 调查第33页标题截断问题 Spec

## Why
第33页标题 "2.3 EXECUTION OF GROUND INVESTIGATION" 翻译后显示为 "2.3..."，文本被过度截断，导致用户无法看到完整的翻译内容。需要调查日志，找出截断的根本原因。

## What Changes
- 调查 pdf_generator.py 中的截断逻辑，分析为什么标题文本被截断到只剩 "2.3..."
- 检查文本框尺寸、字体大小、行高等参数是否合理
- 优化截断策略，避免过度截断

## Impact
- Affected code: `modules/pdf_generator.py`
- 可能影响: 文本渲染逻辑、字体大小计算、文本框尺寸计算

## ADDED Requirements

### Requirement: 调查标题截断根因
系统 SHALL 记录详细的截断日志，包括文本框尺寸、字体大小、行高、原始文本长度、截断后文本长度、截断比例等信息，便于诊断截断原因。

#### Scenario: 标题文本被截断到只剩章节号
- **WHEN** 标题文本 "2.3 EXECUTION OF GROUND INVESTIGATION" 被翻译后渲染
- **THEN** 系统记录完整的截断过程日志：文本框尺寸、字体大小、尝试次数、截断比例
- **THEN** 分析日志找出截断根因：文本框太小？字体太大？行高计算错误？

#### Scenario: 截断比例过低
- **WHEN** 文本被截断到只剩前10%（如 "2.3..."）
- **THEN** 系统记录警告日志，提示截断比例过低，可能影响可读性
- **THEN** 考虑是否需要调整截断策略或文本框尺寸计算逻辑

## MODIFIED Requirements

### Requirement: 截断日志增强
在现有截断日志基础上，增加更多诊断信息：
- 文本框尺寸（宽度、高度）
- 原始字体大小和调整后的字体大小
- 行高倍率
- 每次尝试的详细结果（成功/失败、返回值）
- 截断比例和截断后的文本内容预览

## REMOVED Requirements
无移除需求。