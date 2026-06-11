# 优化翻译提示词避免翻译膨胀 Spec

## Why

LLM 翻译时对短标题做了扩展解释，导致 "MBBR – Process design for BOD (and P) removal"（45 字符）被翻译为 183 字符的扩展段落，超出原始标题框容量，最终在 PDF 渲染时被跳过。根因是翻译 prompt 第 2 条"增加必要的过渡"和第 4 条"句子和段落有长有短"鼓励了扩展行为，与第 6 条"不增删义"存在矛盾。

## What Changes

- 修改 `_generate_system_prompt` 中的规则 2 和规则 4，移除鼓励扩展的表述
- 增加长度约束规则：翻译后文本长度应与原文相近，不添加解释性说明

## Impact

- Affected code:
  - `modules/translator.py` — `_generate_system_prompt` 方法

## ADDED Requirements

### Requirement: 翻译长度约束

系统 SHALL 在翻译 prompt 中明确约束翻译结果的长度，避免 LLM 对原文做扩展解释。

#### Scenario: 翻译标题类短文本
- **WHEN** 翻译器翻译标题类短文本
- **THEN** 翻译结果应保持与原文相近的长度和简洁性
- **AND** 不应添加额外的解释性内容、过渡语句或背景说明

#### Scenario: 翻译正文段落
- **WHEN** 翻译器翻译正文段落
- **THEN** 翻译结果长度应与原文大致相当
- **AND** 不应添加原文中不存在的解释性扩展

## MODIFIED Requirements

### Requirement: 翻译 prompt 规则调整

原有规则 2 "增加必要的过渡" 修改为 "自然过渡"，移除"适当增加过渡词"的表述。

原有规则 4 "书写习惯：句子和段落有长有短" 修改为 "简洁精炼：翻译应简洁精炼，长度与原文相当，不添加解释性说明或扩展内容"。

新增规则：翻译长度应与原文相近，避免翻译膨胀。标题、列表项等短文本尤其应保持简洁。

## REMOVED Requirements

无
