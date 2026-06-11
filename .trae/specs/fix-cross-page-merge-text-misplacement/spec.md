# 修复罗马数字页码未被识别导致跨页错误合并 Spec

## Why

18页开头的文本 "a jumping off point for further exploration" 在PDF翻译后出现在17页右下角页脚位置。根因是17页底部的罗马数字页码 "xv" 未被识别为页脚/页码，保持 `is_body_text=True`，在语义合并阶段与18页第一句话被错误合并为一个 MergedBlock，翻译后18页内容出现在17页的bbox位置。

## 根因分析

### 问题链路

1. 17页底部15%区域有罗马数字页码 "xv"，位于页脚位置
2. `identify_page_numbers()` 只检测阿拉伯数字（`r'\d+'`），不识别罗马数字 → "xv" 不在 `page_number_set` 中
3. `identify_header_footer()` 的相似度检测：罗马数字之间相似度低（"xv" vs "xiv" = 2/3 ≈ 0.667 < 0.8 阈值）→ "xv" 不在 `header_footer_set` 中
4. "xv" 不在 `non_body_texts` 中，保持 `is_body_text=True`
5. 语义合并时 "xv"（17页末尾正文块）与18页首句被合并
6. `MergedBlock.page_num` 取第一个块（17页），18页内容被分配到17页的bbox

### 罗马数字相似度分析

| 文本对 | LCS长度 | 最大长度 | 相似度 | 是否≥0.8阈值 |
|--------|---------|---------|--------|-------------|
| "xv" vs "xiv" | 2 | 3 | 0.667 | 否 |
| "xv" vs "xvi" | 2 | 3 | 0.667 | 否 |
| "xv" vs "xiii" | 2 | 4 | 0.500 | 否 |
| "xii" vs "xiv" | 2 | 3 | 0.667 | 否 |

罗马数字之间的LCS相似度普遍低于0.8阈值，无法通过相似度检测识别为页眉页脚。

### 罗马数字页码在书籍中的常见性

罗马数字页码广泛用于书籍前言、目录等前置部分（front matter），如：
- 前言（Preface）：i-xv
- 目录（Contents）：i-xx
- 序言（Foreword）：i-x

这些页码与正文页码（阿拉伯数字）独立编号，是标准的出版惯例。

## What Changes

- **在 `identify_page_numbers()` 中增加罗马数字页码识别**：检测顶部/底部15%区域的独立罗马数字文本块，识别为页码

## Impact

- Affected code: `modules/extractors/text_analyzer.py` 的 `identify_page_numbers` 函数
- 行为变更：罗马数字页码将被识别为非正文文本，不再参与翻译和语义合并
- 影响范围：所有包含罗马数字页码的PDF文档

## ADDED Requirements

### Requirement: 识别罗马数字页码

系统 SHALL 在 `identify_page_numbers()` 函数中增加罗马数字页码识别，将位于页面顶部或底部15%区域的独立罗马数字文本块识别为页码。

#### Scenario: 独立罗马数字被识别为页码

- **WHEN** 文本块内容为独立罗马数字（如 "xv"、"xii"、"iii"）
- **AND** 文本块位于页面顶部或底部15%区域
- **AND** 文本块字体较小（< 10.0）
- **THEN** 识别为页码，标记为非正文

#### Scenario: 正文中的罗马数字不被误判

- **WHEN** 文本块内容包含罗马数字但不是独立罗马数字（如 "Part III"、"Chapter IV"）
- **AND** 文本块位于页面中间区域
- **THEN** 不被识别为页码

#### Scenario: 罗马数字与阿拉伯数字混合编号

- **WHEN** 文档前置部分使用罗马数字页码，正文部分使用阿拉伯数字页码
- **THEN** 两种页码均被正确识别

### Requirement: 罗马数字正则匹配

系统 SHALL 使用正则表达式匹配标准罗马数字（I, V, X, L, C, D, M 的组合），匹配规则为：
- 仅匹配独立出现的罗马数字（前后无字母连接）
- 支持大小写
- 匹配范围：i-xlix（1-49），覆盖绝大多数书籍前置部分页码

#### Scenario: 匹配常见罗马数字

- **WHEN** 文本为 "xv"、"XII"、"iii"
- **THEN** 正则匹配成功

#### Scenario: 不匹配非罗马数字

- **WHEN** 文本为 "Part III"、"Chapter IV"、"I am"
- **THEN** 正则匹配失败（罗马数字不是独立出现）

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
