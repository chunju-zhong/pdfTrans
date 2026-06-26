# 修复 LLM OCR 藏文识别 Spec

## Why
当源语言为藏文（`bo`）时，LLM OCR 无法正确识别藏文内容：
- DeepSeek-OCR 将藏文页面识别为 `image` 类型而非 `text`，导致藏文内容完全丢失
- 通用 VLM 模型对藏文页面产生英文幻觉输出（如 "The information on the subject is not fully clear..."）
- 根本原因：OCR prompt 中没有语言提示，模型不知道文档是藏文的，无法正确识别和提取

## What Changes
- 在 LLM OCR 的 prompt 中注入源语言信息，告知模型文档的语言
- 对藏文等低资源语言，在 prompt 中增加特别提示，强调必须逐字提取原文而非翻译或描述
- 将 `source_lang` 参数从 `translation_service` 传递到 `LlmOcrExtractor`

## Impact
- Affected code:
  - `modules/ocr/llm_extractor.py` — prompt 构建逻辑、构造函数
  - `services/translation_service.py` — 传递 `source_lang` 到 OCR 提取器
  - `modules/pdf_extractor.py` — 传递 `source_lang` 到 OCR 提取器

## ADDED Requirements

### Requirement: LLM OCR prompt 注入源语言信息
LLM OCR 提取器 SHALL 在 prompt 中包含源语言信息，使模型知道文档的语言。

#### Scenario: DeepSeek-OCR 模型处理藏文文档
- **WHEN** 源语言为藏文（`bo`）且使用 DeepSeek-OCR 模型
- **THEN** prompt 中包含藏文语言提示，告知模型文档为藏文，要求逐字提取藏文原文
- **AND** 藏文文本被识别为 `text` 类型而非 `image` 类型

#### Scenario: 通用 VLM 模型处理藏文文档
- **WHEN** 源语言为藏文（`bo`）且使用通用 VLM 模型
- **THEN** system prompt 中包含藏文语言提示
- **AND** 模型输出藏文原文而非英文幻觉

#### Scenario: 非藏文文档不受影响
- **WHEN** 源语言为英文（`en`）或其他已有语言
- **THEN** OCR 行为与修改前一致，无回归

### Requirement: source_lang 参数传递链路
translation_service SHALL 将 `source_lang` 传递到 `PdfExtractor`，再传递到 `LlmOcrExtractor`。

#### Scenario: 翻译服务调用 OCR 提取
- **WHEN** 用户选择源语言为 `bo`（藏文）并启用 LLM OCR
- **THEN** `source_lang` 参数从 `translation_service` → `PdfExtractor` → `LlmOcrExtractor` 完整传递
