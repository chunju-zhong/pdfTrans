# 修复翻译垃圾输出回退机制 Spec

## Why
当翻译内容包含特殊模式（如分词器输出 `['▁The', '▁addition'...]`）时，LLM 可能产生大量重复垃圾输出（如数千个 `'▁'`），导致原文208字符产出10268字符译文。当前系统仅记录 WARNING 日志就继续使用截断的垃圾结果，没有任何质量拦截或回退机制，垃圾内容直接进入下游拆分和渲染流程。

## What Changes
- 在翻译结果返回后增加异常膨胀检测：译文长度超过原文 N 倍时判定为异常
- 增加重复模式检测：检测翻译结果中是否存在大量重复片段
- 检测到异常输出时，回退使用原文而非垃圾译文
- 截断（finish_reason=length）场景下，同样触发异常检测，不再仅记录 WARNING

## Impact
- Affected code: `services/translation_content.py`（`translate_merged_block` 和 `translate_original_block`）
- Affected code: `modules/translator.py`（`_postprocess_text`）

## ADDED Requirements

### Requirement: 翻译结果异常膨胀检测
系统 SHALL 在翻译结果返回后检测译文长度是否异常膨胀（译文长度超过原文长度的 5 倍时判定为异常）。

#### Scenario: 译文长度异常膨胀
- **WHEN** 翻译结果返回，且译文长度超过原文长度的 5 倍
- **THEN** 系统记录 WARNING 日志，包含原文长度和译文长度
- **THEN** 系统回退使用原文作为翻译结果

#### Scenario: 译文长度正常
- **WHEN** 翻译结果返回，且译文长度不超过原文长度的 5 倍
- **THEN** 正常使用翻译结果，行为不变

### Requirement: 翻译结果重复模式检测
系统 SHALL 检测翻译结果中是否存在大量重复片段（同一子串连续重复超过 10 次或占译文超过 30%）。

#### Scenario: 翻译结果包含大量重复片段
- **WHEN** 翻译结果中同一子串连续重复超过 10 次，或重复内容占译文超过 30%
- **THEN** 系统记录 WARNING 日志，包含重复模式信息
- **THEN** 系统回退使用原文作为翻译结果

#### Scenario: 翻译结果无异常重复
- **WHEN** 翻译结果中无异常重复模式
- **THEN** 正常使用翻译结果，行为不变

### Requirement: 截断场景联动异常检测
系统 SHALL 在检测到翻译被截断（finish_reason=length）时，同时执行异常膨胀检测和重复模式检测，而非仅记录 WARNING。

#### Scenario: 截断且输出异常
- **WHEN** 翻译被截断且异常检测判定输出为垃圾
- **THEN** 系统回退使用原文，记录 WARNING 日志

#### Scenario: 截断但输出正常
- **WHEN** 翻译被截断但异常检测判定输出正常
- **THEN** 使用截断的翻译结果（保留现有行为，因为截断内容可能仍有价值）

## MODIFIED Requirements

### Requirement: 翻译结果后处理
在 `_postprocess_text` 和 `translate_merged_block`/`translate_original_block` 中，增加异常输出检测和回退逻辑。检测到异常输出时回退到原文，而非继续使用垃圾译文。
