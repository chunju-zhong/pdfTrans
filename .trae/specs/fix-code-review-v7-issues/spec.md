# 修复 Code Review v7 Issues Spec

## Why
Code Review 发现 6 个问题：(1) `_parse_format_result` 的 sentinel `["fallback_invalid_format"]` 在单块+空响应时长度恰好等于 expected_count，导致哨兵字符串被写入译文（数据损坏）；(2) `_build_short_english_hint` 全部逻辑被注释，恒返回 `""`，`_SOURCE_LANG_ENGLISH_NAMES` 字典仅在注释代码中引用（死代码）；(3) `format_blocks` 静默吞掉所有 API 异常返回原文，调用方的 `task.add_warning` 永远不触发，用户不知道排版被跳过；(4) `llm_response_parser.py` 误加 `numpy`/`PIL` 未使用导入；(5) `format_blocks` 接收 `target_lang` 但从未使用；(6) `format_blocks` 异常处理使用原始 `str(e)` 而非 `classify_llm_error` 的友好消息，与代码库其余部分不一致。

## What Changes
- **Issue 1** (HIGH): `_parse_format_result` 失败时返回 `[]`（空列表）而非 `["fallback_invalid_format"]`，确保 `len([]) != expected_count` 恒成立以触发整页回退
- **Issue 2** (MEDIUM): 删除 `_build_short_english_hint` 方法、`_SOURCE_LANG_ENGLISH_NAMES` 字典，简化 `_extract_page` 中 DeepSeek-OCR 分支（直接使用 `DEEPSEEK_OCR_PROMPT`）
- **Issue 3** (MEDIUM): `format_blocks` 移除内部 try/except，让异常向上抛出由调用方 `translation_content.py` 的 `task.add_warning` 统一上报 UI
- **Issue 4** (LOW): 删除 `llm_response_parser.py` 中未使用的 `numpy`/`PIL` 导入
- **Issue 5** (LOW): `format_blocks` 在 user prompt 中注入目标语言名称，使 LLM 能按目标语言排版规范优化（标点、间距等）
- **Issue 6** (LOW): `format_blocks` 异常处理改用 `classify_llm_error(e)`（与 Issue 3 合并实现：异常向上抛出时由调用方使用 `classify_llm_error`）

## Impact
- Affected specs: fix-format-blocks-llm-dropping-markers（`_parse_format_result` 行为变更）、fix-deepseek-ocr-short-english-hint（删除死代码方法）
- Affected code: `modules/translator.py`、`modules/ocr/llm_extractor.py`、`modules/ocr/llm_response_parser.py`、`services/translation_content.py`、`tests/test_translator.py`

## ADDED Requirements

### Requirement: format_blocks 失败时返回空列表触发整页回退
系统 SHALL 在 `_parse_format_result` 解析失败（无标记且行级回退不足）时返回空列表 `[]`，使调用方 `format_blocks` 的长度检查 `len(cleaned) != len(translated_texts)` 恒为 True，从而回退到原文。

#### Scenario: 单块 + LLM 返回空响应
- **WHEN** `format_blocks` 接收 1 个文本块且 LLM 返回空/空白响应
- **THEN** `_parse_format_result` 返回 `[]`
- **AND** `format_blocks` 检测到 `len([]) != 1`，回退返回原文
- **AND** 不会将哨兵字符串写入译文输出

### Requirement: format_blocks 异常上报 UI
系统 SHALL 让 `format_blocks` 内部的 API 异常向上抛出，由调用方 `translation_content.py` 捕获并通过 `task.add_warning` 上报 UI。

#### Scenario: format_blocks API 调用失败
- **WHEN** `format_blocks` 内 LLM API 调用抛出异常
- **THEN** 异常向上传播到 `translation_content.py` 的 try/except
- **AND** 调用方调用 `task.add_warning("排版失败，已回退到未排版译文", ...)`
- **AND** 用户在 UI 看到排版失败警告

### Requirement: format_blocks 使用目标语言提示
系统 SHALL 在 `format_blocks` 的 user prompt 中注入目标语言名称，使 LLM 能按目标语言的排版规范优化标点和间距。

#### Scenario: 中文目标语言
- **WHEN** `format_blocks` 被调用且 `target_lang="zh"`
- **THEN** user prompt 包含目标语言提示（如"目标语言为中文"）
- **AND** LLM 按中文排版规范优化标点（。，！？）和 CJK 间距

## REMOVED Requirements

### Requirement: _build_short_english_hint 方法
**Reason**: 该方法全部逻辑被注释，恒返回 `""`，且 `_SOURCE_LANG_ENGLISH_NAMES` 仅在注释代码中引用。DeepSeek-OCR 分支已直接使用 `DEEPSEEK_OCR_PROMPT`，该方法为死代码。
**Migration**: 删除 `_build_short_english_hint` 方法、`_SOURCE_LANG_ENGLISH_NAMES` 字典，简化 `_extract_page` DeepSeek-OCR 分支移除 `short_hint` 判断。

### Requirement: format_blocks 内部异常吞没
**Reason**: `format_blocks` 内部 `except Exception` 吞掉所有异常返回原文，导致调用方的 `task.add_warning` 永远不触发，用户无法感知排版失败。
**Migration**: 移除 `format_blocks` 内部 try/except，让异常向上抛出由调用方统一处理。

### Requirement: _parse_format_result 哨兵字符串
**Reason**: `["fallback_invalid_format"]` 哨兵列表长度为 1，当 expected_count 恰好为 1 时长度检查失效，哨兵字符串被写入译文。
**Migration**: 失败时返回 `[]` 空列表。
