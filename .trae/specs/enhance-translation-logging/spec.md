# 增强翻译步骤日志可观测性 Spec

## Why

18页翻译问题的排查中，翻译步骤的 INFO 日志完全缺失（日志文件只有73行），导致无法确认翻译 API 是否被调用、返回了什么结果。需要增强翻译步骤的日志可观测性，确保关键信息写入文件。

## What Changes

- **FileHandler 启用即时刷新**：`logging_config.py` 中为 `FileHandler` 设置 `flush` 行为，确保日志即时写入磁盘
- **翻译步骤增加详细日志**：在 `translate_original_block` 和 `translate_merged_block` 中增加翻译 API 原始响应日志
- **翻译结果与原文相同时记录 WARNING**：当翻译结果与原文相同时（可能翻译失败），记录 WARNING 日志

## Impact

- Affected code: `utils/logging_config.py`、`services/translation_service.py`、`modules/translator.py`

## ADDED Requirements

### Requirement: FileHandler 即时刷新

日志 FileHandler SHALL 在每次写入后刷新到磁盘，确保进程异常退出时日志不丢失。

#### Scenario: 翻译步骤日志即时写入

- **WHEN** 翻译步骤产生 INFO 级别日志
- **THEN** 日志立即写入 `app.log` 文件，不依赖缓冲区刷新

### Requirement: 翻译步骤详细日志

翻译步骤 SHALL 记录以下详细信息：
1. 翻译请求的原文（前100字符）
2. 翻译 API 的原始响应（前200字符）
3. 翻译结果的文本（前200字符）
4. 翻译结果的 token 使用量

#### Scenario: 翻译成功

- **WHEN** 翻译 API 返回翻译结果
- **THEN** 记录 INFO 日志：原文前100字符、翻译结果前200字符、token 使用量

#### Scenario: 翻译失败

- **WHEN** 翻译 API 调用异常
- **THEN** 记录 ERROR 日志：原文前100字符、异常信息

### Requirement: 翻译结果与原文相同时记录 WARNING

当翻译结果与原文完全相同时，SHALL 记录 WARNING 日志，提示可能翻译失败。

#### Scenario: 翻译结果与原文相同

- **WHEN** `translated_text == original_text`
- **THEN** 记录 WARNING 日志：`翻译结果与原文相同，可能翻译失败: {text[:100]}`

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
