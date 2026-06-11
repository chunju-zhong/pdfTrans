# 修复非OCR翻译PDF显示问号 Spec

## Why

非OCR翻译PDF时，`_get_suitable_font()` 第1步尝试使用PDF内嵌的原始英文字体（如 `TimesNewRomanPSMT`），插入成功后直接返回。但英文字体可能不包含目标语言的字符（如中文、泰语、俄语等），无法渲染这些字符，导致翻译文本显示为问号。OCR路径因 `TextBlock.font` 为空字符串而跳过此步，能正确找到支持目标语言的系统字体。

此外，`_check_font_support()` 方法对非 zh/ja/ko 语言直接返回 `True`，导致泰语、越南语、俄语等语言无法正确检测字体支持。

## What Changes

- **在 `_get_suitable_font()` 第1步中增加原始字体的目标语言支持检测**：即使原始字体插入成功，也要验证其是否支持目标语言字符，不支持则跳过继续搜索系统字体
- **扩展 `_check_font_support()` 为所有语言统一检测**：移除对非 zh/ja/ko 语言直接返回 `True` 的短路逻辑，为所有语言提供测试字符进行实际检测

## Impact

- Affected code: `modules/pdf_generator.py` 的 `_get_suitable_font()` 和 `_check_font_support()` 方法
- 行为变更：非OCR路径翻译为任何字体不支持的语言时，不再使用PDF内嵌的英文字体，改为使用支持目标语言的系统字体

## ADDED Requirements

### Requirement: 原始字体目标语言支持检测

系统 SHALL 在 `_get_suitable_font()` 中，当原始字体插入成功后，检查该字体是否支持目标语言的字符。若不支持，则跳过并继续搜索系统字体。

#### Scenario: 非OCR路径翻译为中文，原始英文字体不支持中文

- **WHEN** `original_font` 为 `"TimesNewRomanPSMT"`（PDF内嵌英文字体），`target_lang` 为 `"zh"`
- **AND** `page.insert_font(fontname=original_font, fontfile=None)` 成功
- **THEN** 系统检测到该字体不支持中文字符，跳过此字体
- **AND** 继续搜索系统字体，返回支持中文的字体（如 `PingFang SC`）

#### Scenario: 非OCR路径翻译为英文，原始字体支持英文

- **WHEN** `original_font` 为 `"TimesNewRomanPSMT"`，`target_lang` 为 `"en"`
- **THEN** 系统检测到该字体支持英文字符，直接返回原始字体名

#### Scenario: OCR路径翻译为中文

- **WHEN** `original_font` 为空字符串，`target_lang` 为 `"zh"`
- **THEN** 跳过第1步，继续搜索系统字体（行为不变）

### Requirement: 统一字体支持检测

系统 SHALL 对所有目标语言统一使用测试字符进行字体支持检测，不再对非 zh/ja/ko 语言直接返回 `True`。每种语言使用其特有的测试字符，确保字体真正包含该语言的字形。

#### Scenario: 泰语字体检测

- **WHEN** `target_lang` 为 `"th"`，字体不支持泰语字符
- **THEN** `_check_font_support()` 返回 `False`

#### Scenario: 德语字体检测

- **WHEN** `target_lang` 为 `"de"`，字体包含德语特殊字符（ä, ö, ü, ß）
- **THEN** `_check_font_support()` 返回 `True`

#### Scenario: 中文字体检测

- **WHEN** `target_lang` 为 `"zh"`，字体不包含中文字符
- **THEN** `_check_font_support()` 返回 `False`

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
