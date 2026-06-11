# 翻译优化：不解释和翻译公式与缩写 Spec

## Why

当前翻译流程中，OCR 提取的公式（LaTeX 字符串）被当作普通文本发送给 LLM 翻译，导致公式被破坏、误译或添加解释性文字。缩写（如 AI、LLM、RAG）也没有专门的保护规则，翻译不一致。提示词中已有"不翻译URL"和"不翻译代码段"的明确规则，但公式和缩写缺乏同等保护。

## What Changes

* TextBlock 新增 `is_formula` 属性，标记公式块

* OCR 提取时为公式 TextBlock 设置 `is_formula=True`

* 翻译服务中跳过 `is_formula=True` 的文本块，不发送给 LLM

* 翻译提示词新增规则：不翻译公式、不解释缩写（两种模式均生效）

## Impact

* Affected code: `models/text_block.py`、`modules/ocr/paddle_extractor.py`、`services/translation_service.py`、`modules/translator.py`

* Affected specs: 无冲突

## ADDED Requirements

### Requirement: 公式块标记与跳过翻译（OCR 模式）

系统 SHALL 在 OCR 提取时标记公式 TextBlock，翻译时跳过公式块不进行翻译。

#### Scenario: OCR 模式公式块被标记

* **WHEN** OCR 步骤3识别出 LaTeX 公式并创建 TextBlock

* **THEN** 该 TextBlock 的 `is_formula` 属性为 `True`

#### Scenario: OCR 模式公式块跳过翻译

* **WHEN** 翻译服务遍历文本块进行翻译

* **THEN** `is_formula=True` 的文本块不发送给 LLM，翻译结果直接使用原文（LaTeX 字符串）

#### Scenario: 公式块仍参与渲染

* **WHEN** PDF 生成阶段渲染翻译后的页面

* **THEN** 公式块使用原始 LaTeX 文本渲染，与翻译后的文本块一起正常显示

### Requirement: 非 OCR 模式公式保护

非 OCR 模式下 PyMuPDF 提取的文本中没有公式结构信息，公式混在普通文本中，无法通过结构化方式识别。系统 SHALL 通过翻译提示词规则保护公式。

#### Scenario: 非 OCR 模式公式嵌入在文本中

* **WHEN** PyMuPDF 提取的文本块中包含公式（如 "根据 E=mc² 可知" 或 "其中 α=0.05"）

* **THEN** 翻译提示词规则指导 LLM 保持公式原样，不翻译、不解释

#### Scenario: 非 OCR 模式无法结构化跳过

* **WHEN** 非 OCR 模式下的文本块

* **THEN** 所有文本块均发送给 LLM 翻译，依赖提示词规则保护公式

### Requirement: 翻译提示词保护公式和缩写（两种模式均生效）

系统 SHALL 在翻译提示词中新增公式和缩写的保护规则，对 OCR 和非 OCR 模式均有效。

#### Scenario: 提示词包含公式保护规则

* **WHEN** 生成翻译系统提示词

* **THEN** 包含规则"不要翻译公式：原文中包含的数学公式、LaTeX 表达式、数学符号（如 $...$、\frac{}{}、α、β、∑ 等），保持原状，不进行翻译，不添加解释"

#### Scenario: 提示词包含缩写保护规则

* **WHEN** 生成翻译系统提示词

* **THEN** 包含规则"不要解释缩写：原文中的专业缩写（如 AI、LLM、API、CPU 等），保持原状，不展开解释，不添加括号说明"

## MODIFIED Requirements

### Requirement: TextBlock 支持公式标记

TextBlock 类新增 `is_formula` 属性（默认 `False`），用于区分公式块和普通文本块。非 OCR 模式下所有 TextBlock 的 `is_formula` 保持默认 `False`。

## 双模式保护策略总结

| 模式       | 公式保护方式                                             | 缩写保护方式 |
| -------- | -------------------------------------------------- | ------ |
| OCR 模式   | 结构化跳过（`is_formula=True` 块不翻译）+ 提示词规则（保护嵌入文本中的公式片段） | 提示词规则  |
| 非 OCR 模式 | 提示词规则（无法结构化识别，依赖 LLM 遵循规则）                         | 提示词规则  |

