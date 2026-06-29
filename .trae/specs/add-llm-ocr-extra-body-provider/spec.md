# LLM OCR extra_body Provider 配置 Spec

## Why
LLM OCR 调用 OpenAI 兼容 API 时，部分服务商（如 aiping.cn）支持通过 `extra_body` 参数指定 provider 路由，以选择特定的模型服务商。当前代码未传递 `extra_body`，无法控制请求路由到指定服务商。

## What Changes
- 在 `config.py` 中新增 `OCR_LLM_EXTRA_BODY` 配置项，从环境变量读取 JSON 字符串
- 在 `LlmOcrExtractor._extract_page` 的 API 调用中，将 `extra_body` 传递给 `client.chat.completions.create()`

## Impact
- Affected code:
  - `config.py` — 新增 `OCR_LLM_EXTRA_BODY` 配置
  - `modules/ocr/llm_extractor.py` — API 调用增加 `extra_body` 参数

## ADDED Requirements

### Requirement: LLM OCR extra_body 配置
系统 SHALL 支持通过环境变量配置 LLM OCR API 调用的 `extra_body` 参数，用于指定 provider 路由。

#### Scenario: 配置了 OCR_LLM_EXTRA_BODY 环境变量
- **WHEN** 环境变量 `OCR_LLM_EXTRA_BODY` 设置为 `{"provider": {"order": ["目标服务商名称"]}}`
- **THEN** LLM OCR 的 API 调用中包含 `extra_body={"provider": {"order": ["目标服务商名称"]}}`
- **AND** 请求被路由到指定服务商

#### Scenario: 未配置 OCR_LLM_EXTRA_BODY 环境变量
- **WHEN** 环境变量 `OCR_LLM_EXTRA_BODY` 未设置或为空
- **THEN** LLM OCR 的 API 调用不传递 `extra_body` 参数，行为与修改前一致

#### Scenario: OCR_LLM_EXTRA_BODY 环境变量格式错误
- **WHEN** 环境变量 `OCR_LLM_EXTRA_BODY` 的值不是有效 JSON
- **THEN** 系统记录警告日志，跳过 `extra_body` 参数，不中断 OCR 流程
