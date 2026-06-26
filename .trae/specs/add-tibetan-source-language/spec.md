# 新增藏文源语言 Spec

## Why
当前系统支持 8 种源语言（中/英/日/韩/法/德/西/俄），缺少藏文（Tibetan）支持。藏文是中国重要的少数民族语言，有实际的 PDF 翻译需求。

## What Changes
- 在所有语言映射字典中新增藏文条目，语言代码为 `bo`（ISO 639-2/T），显示名称为 `藏文`
- 在 PDF 生成器的字体检测逻辑中新增藏文测试字符，确保藏文输出时能正确选择支持藏文的字体

## Impact
- Affected code:
  - `config.py` — `SUPPORTED_LANGUAGES`
  - `modules/translator.py` — `supported_languages`
  - `modules/aiping_translator.py` — `lang_map`
  - `modules/silicon_flow_translator.py` — `lang_map`
  - `modules/semantic_analyzer.py` — `supported_languages`
  - `modules/pdf_generator.py` — 两处 `test_chars` 字典

## ADDED Requirements

### Requirement: 藏文源语言支持
系统 SHALL 支持藏文（`bo`）作为源语言和目标语言。

#### Scenario: 用户选择藏文作为源语言
- **WHEN** 用户在 Web 界面或 CLI 中选择 `bo`（藏文）作为源语言
- **THEN** 系统接受该选择，翻译提示词中正确显示"藏文"作为源语言名称

#### Scenario: 藏文作为目标语言时字体检测
- **WHEN** 目标语言为藏文（`bo`）
- **THEN** PDF 生成器使用藏文测试字符（如 `བཀྲ་ཤིས་བདེ་ལེགས`）检测字体是否支持藏文字形
- **AND** 不支持藏文的字体被正确排除，系统回退到支持藏文的系统字体

#### Scenario: 语义分析和术语提取
- **WHEN** 源语言为藏文时
- **THEN** 语义分析器和术语提取器正确识别藏文语言名称，在提示词中使用"藏文"
