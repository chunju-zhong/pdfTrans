# 保持翻译中列表格式 Spec

## Why

翻译时列表格式丢失，例如原文 "Overflow surface load, • 5,0 m/h at Qdim • 7,8 m/h at Qmaksdim" 中的列表项分隔符 `•` 和换行被合并为连续文本。根因是 `_preprocess_text` 和 `_postprocess_text` 用 `' '.join(text.split())` 将所有换行替换为空格，破坏了列表项之间的格式分隔。

## What Changes

- 修改 `_preprocess_text`：保留列表项之间的换行符，只压缩多余空白
- 修改 `_postprocess_text`：保留列表项之间的换行符，只压缩多余空白
- 在翻译 prompt 中增加列表格式保持规则

## Impact

- Affected code:
  - `modules/translator.py` — `_preprocess_text`、`_postprocess_text`、`_generate_system_prompt`

## 根因分析

### 问题链路

1. **OCR 提取**：PaddleOCR 的 `block.content` 返回的文本中，列表项之间用 `\n` 分隔（如 `"Overflow surface load,\n• 5,0 m/h at Qdim\n• 7,8 m/h at Qmaksdim"`）

2. **预处理破坏**：[translator.py:129](file:///Users/chunju/work/pdfTrans/modules/translator.py#L129) 的 `_preprocess_text` 用 `' '.join(text.split())` 将所有换行替换为空格，列表项分隔消失

3. **翻译后处理破坏**：[translator.py:71](file:///Users/chunju/work/pdfTrans/modules/translator.py#L71) 的 `_postprocess_text` 同样用 `' '.join(processed_text.split())` 将所有换行替换为空格，即使 LLM 在翻译结果中保留了换行也会被消除

4. **语义合并**：[text_processing.py:170](file:///Users/chunju/work/pdfTrans/utils/text_processing.py#L170) 合并块时用空格连接，进一步消除格式

### 修复策略

将 `' '.join(text.split())` 替换为保留换行的版本：先按 `\n` 分割，每行内压缩空白，再用 `\n` 重新连接。这样列表项之间的换行得以保留，同时每行内的多余空白被清理。

## ADDED Requirements

### Requirement: 翻译预处理保留列表格式

系统 SHALL 在翻译预处理和后处理中保留列表项之间的换行符，不将其替换为空格。

#### Scenario: 原文包含列表项换行
- **WHEN** 原文文本中包含换行符分隔的列表项（如 `• item1\n• item2`）
- **THEN** 预处理后应保留列表项之间的换行符
- **AND** 每行内的多余空白应被压缩

#### Scenario: 翻译结果包含列表项换行
- **WHEN** LLM 翻译结果中保留了列表项之间的换行符
- **THEN** 后处理后应保留这些换行符
- **AND** 不应将换行符替换为空格

### Requirement: 翻译 prompt 列表格式保持

系统 SHALL 在翻译 prompt 中增加列表格式保持规则。

#### Scenario: 翻译包含列表项的文本
- **WHEN** 翻译器翻译包含列表项的文本
- **THEN** 翻译结果应保持原文的列表格式（换行、项目符号等）
- **AND** 不应将列表项合并为连续段落

## MODIFIED Requirements

无

## REMOVED Requirements

无
