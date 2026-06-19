# 修复 LLM OCR 响应解析失败 Spec

## Why
LLM OCR 使用 DeepSeek-OCR 模型时，当前代码发送自定义中文 prompt 要求返回 JSON 格式，但 DeepSeek-OCR 模型有自己专用的 prompt 格式（`<image>\n<|grounding|>...`），不遵循自定义 JSON 输出要求，导致响应解析失败，所有页面提取到 0 个文本块。

## What Changes
- 修改 `LlmOcrExtractor` 的 prompt 格式，适配 DeepSeek-OCR 模型的原生格式
- 修改响应解析逻辑，支持 DeepSeek-OCR 的 `<|ref|>...<|/ref|>` 标签和 Markdown 输出
- 添加原始响应日志，便于调试
- 支持 `response_format: {"type": "json_object"}` 强制 JSON 输出（平台支持时）

## Impact
- Affected code: `modules/ocr/llm_extractor.py`
- Affected specs: `simplify-llm-ocr-config`

## MODIFIED Requirements

### Requirement: DeepSeek-OCR prompt 格式
LLM OCR 调用 DeepSeek-OCR 模型时 SHALL 使用模型原生的 prompt 格式。

#### Scenario: DeepSeek-OCR 基础 OCR 提取
- **WHEN** 使用 DeepSeek-OCR 模型提取页面内容
- **THEN** prompt 使用 `<image>\n<|grounding|>OCR this image.` 格式（模型原生格式）

#### Scenario: DeepSeek-OCR Markdown 输出
- **WHEN** 使用 DeepSeek-OCR 模型并需要结构化输出
- **THEN** prompt 使用 `<image>\n<|grounding|>Convert the document to markdown.` 格式

### Requirement: DeepSeek-OCR 响应解析
LLM OCR SHALL 支持 DeepSeek-OCR 模型的原生响应格式。

#### Scenario: 响应包含 `<|ref|>` 标签
- **WHEN** DeepSeek-OCR 返回包含 `<|ref|>text<|/ref|>` 标签的响应
- **THEN** 提取标签内的文本内容，映射为 TextBlock

#### Scenario: 响应为 Markdown 格式
- **WHEN** DeepSeek-OCR 返回 Markdown 格式的文本
- **THEN** 按段落分割，映射为 TextBlock

#### Scenario: 响应为 JSON 格式（兼容旧逻辑）
- **WHEN** 模型返回有效的 JSON
- **THEN** 按现有 JSON 解析逻辑处理

### Requirement: 原始响应日志
LLM OCR 提取每页时 SHALL 记录原始响应的前 500 字符，便于调试。

#### Scenario: 提取成功
- **WHEN** LLM OCR 收到响应
- **THEN** 日志记录 `result_text[:500]`

#### Scenario: 提取失败
- **WHEN** JSON 解析失败
- **THEN** 日志记录 `result_text[:500]`，WARNING 级别
