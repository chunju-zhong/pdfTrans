# 更新SKILL.md添加LLM OCR功能文档 Spec

## Why
SKILL.md 中的 OCR 部分仅记录了 PaddleOCR 引擎，但代码中已完整实现了 LLM 视觉模型 OCR 引擎（`--ocr-engine llm`），支持 DeepSeek-OCR、Qwen3-VL 等模型。SKILL.md 缺少对 LLM OCR 功能的文档说明，导致用户无法了解和使用该功能。

## What Changes
- 更新 OCR 参数说明：`--ocr-engine` 支持 `paddleocr` 和 `llm` 两个选项
- 新增 LLM OCR 引擎功能说明（支持的模型、工作原理、响应格式）
- 新增 LLM OCR 相关环境变量配置说明
- 新增 LLM OCR 使用示例
- 更新 OCR 模式说明章节，区分 PaddleOCR 和 LLM 两种引擎

## Impact
- Affected code: `SKILL.md`（文档文件）
- Affected specs: 无代码变更，仅文档更新

## ADDED Requirements

### Requirement: LLM OCR 引擎文档
SKILL.md SHALL 包含 LLM OCR 引擎的完整功能说明，包括：
- 引擎类型选项（paddleocr / llm）
- LLM OCR 支持的模型（DeepSeek-OCR、Qwen3-VL 等）
- LLM OCR 的工作原理（通过 OpenAI 兼容 API 调用视觉模型）
- LLM OCR 的两种响应格式（JSON 格式和 DeepSeek-OCR 原生 Markdown/<|ref|> 格式）
- LLM OCR 相关环境变量配置
- LLM OCR 使用示例

#### Scenario: 用户查看 SKILL.md 了解 LLM OCR
- **WHEN** 用户阅读 SKILL.md 的 OCR 部分
- **THEN** 能看到 `--ocr-engine llm` 选项及其说明
- **AND** 能看到 LLM OCR 的使用示例
- **AND** 能看到 LLM OCR 相关的环境变量配置

### Requirement: OCR 参数说明更新
SKILL.md 中 `--ocr-engine` 参数 SHALL 标注支持 `paddleocr` 和 `llm` 两个选项。

#### Scenario: 用户查看 OCR 参数
- **WHEN** 用户查看 `--ocr-engine` 参数说明
- **THEN** 能看到可选值为 `paddleocr`（默认）和 `llm`

## MODIFIED Requirements

### Requirement: OCR模式说明
OCR模式说明章节 SHALL 区分 PaddleOCR 和 LLM 两种引擎，分别说明各自的功能特点、适用场景和注意事项。

## REMOVED Requirements
无
