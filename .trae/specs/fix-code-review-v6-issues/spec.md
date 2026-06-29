# 修复 Code Review v6 Issues Spec

## Why
Code Review 发现 5 个问题：(1) `OCR_LLM_TIMEOUT` 配置未接入客户端初始化导致配置不生效；(2) `OCR_LLM_EXTRA_BODY` 死配置误导维护者；(3) 超时错误检查逻辑在 3 处重复违反 DRY；(4) 超时消息硬编码 "120秒" 而非使用配置值；(5) 未使用的异常变量 `e`。

## What Changes
- **Issue 1** (HIGH): `config.OCR_LLM_TIMEOUT` 接入 OpenAI 客户端初始化 `timeout` 参数
- **Issue 2** (MEDIUM): 删除 `OCR_LLM_EXTRA_BODY` 死配置
- **Issue 3** (MEDIUM): 提取共享方法 `_handle_ocr_timeout_errors()` 消除 3 处重复
- **Issue 4** (MEDIUM): 超时消息改为引用 `config.OCR_LLM_TIMEOUT` 动态值
- **Issue 5** (LOW): 移除 `except APITimeoutError as e:` 中未使用的 `e`

## Impact
- Affected specs: fix-llm-ocr-timeout-error-message（此前 Spec 的代码被优化）
- Affected code: `config.py`、`modules/ocr/llm_extractor.py`、`services/translation_service.py`

## ADDED Requirements

### Requirement: OCR_LLM_TIMEOUT 配置生效
系统 SHALL 在初始化 OpenAI 客户端时使用 `config.OCR_LLM_TIMEOUT` 值设置 `timeout` 参数，而非硬编码值。

#### Scenario: 客户端初始化
- **WHEN** `LlmOcrExtractor.client` 属性首次访问创建 OpenAI 客户端
- **THEN** `timeout` 参数使用 `config.OCR_LLM_TIMEOUT` 的值
- **AND** 用户可通过环境变量 `OCR_LLM_TIMEOUT` 控制超时时间

### Requirement: 超时消息使用配置值
系统 SHALL 在生成超时错误消息时引用 `config.OCR_LLM_TIMEOUT` 而非硬编码的 "120秒"。

#### Scenario: 超时错误消息
- **WHEN** LLM OCR 请求超时生成错误消息
- **THEN** 消息中包含 `config.OCR_LLM_TIMEOUT` 的实际值（如 "300秒"）

### Requirement: 提取通用错误处理方法
系统 SHALL 将检查 OCR 提取超时错误的重复逻辑提取为共享方法。

#### Scenario: 所有检查点共用同一方法
- **WHEN** `missing_pages`、`has_matching_pages`、`text_blocks` 三个检查点判定提取结果为空
- **THEN** 调用 `_handle_ocr_timeout_errors(task, ocr_extract_errors)` 方法处理超时情况
- **AND** 该方法返回 `bool` 指示是否已处理（已处理则上层直接 `return None`）

## REMOVED Requirements

### Requirement: OCR_LLM_EXTRA_BODY 配置
**Reason**: 该配置项定义后从未被任何代码引用，属于死代码，会误导维护者认为有 provider 路由功能。
**Migration**: 直接删除 `config.py` 中的 `OCR_LLM_EXTRA_BODY` 定义。
