# 清除翻译结果中的元注释 Spec

## Why

尽管已在翻译 prompt 中添加规则 13 "禁止元注释"，LLM 仍然在翻译结果中添加解释翻译决策的元注释，例如 "（注：原文存在排版断裂问题，根据上下文逻辑进行语义衔接，"Gives the opportunity of CEPT"译为"为采用CEPT工艺提供了可能"……）"。纯 prompt 约束不足以阻止此行为，需要在后处理阶段自动清除。

## What Changes

- 在 `Translator._postprocess_text` 中增加元注释检测和清除逻辑
- 使用正则匹配常见的元注释模式，将其从翻译结果中移除

## Impact

- Affected code:
  - `modules/translator.py` — `_postprocess_text` 方法

## ADDED Requirements

### Requirement: 翻译结果元注释自动清除

系统 SHALL 在翻译后处理阶段自动检测并清除 LLM 添加的元注释，确保翻译结果只包含翻译内容本身。

#### Scenario: 翻译结果包含括号内的注释说明
- **WHEN** 翻译结果中包含以"（注："、"（说明："、"（备注："等开头的括号内注释
- **THEN** 系统应自动移除该注释及其括号
- **AND** 移除后应清理多余的空格

#### Scenario: 翻译结果包含"注："开头的独立说明
- **WHEN** 翻译结果末尾包含以"注："、"说明："等开头的独立说明语句
- **THEN** 系统应自动移除该说明语句
- **AND** 移除后应清理多余的空格

#### Scenario: 翻译结果包含引号内的翻译决策解释
- **WHEN** 翻译结果中包含类似 `"XXX"译为"YYY"` 的翻译决策解释
- **THEN** 系统应自动移除包含此类解释的整个注释块

#### Scenario: 正常翻译内容不受影响
- **WHEN** 翻译结果中包含正常的括号内容（如技术术语的缩写解释）
- **THEN** 系统不应移除该内容
- **AND** 只有以"注："、"说明："、"备注："等元注释标记开头的内容才会被移除

## MODIFIED Requirements

无

## REMOVED Requirements

无
