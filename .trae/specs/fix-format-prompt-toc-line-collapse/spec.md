# 修复目录排版换行丢失 Spec

## Why

目录页（如第 12-13 页）翻译后排版丢失，原本逐行的目录条目被堆成一两个连续文本块。以 app.log（任务 04477b97，2026-06-27 09:56）实测为例：

```
页面 12 块 3: 格式排版 'x \n| \n目录...' -> 'x | 目录...'   # 换行被合并为空格
页面 13 块 4: 格式排版 '目录 \n| \nxi...' -> '目录 xi...'   # 换行被合并为空格
```

每个目录条目本应单独一行（`条目文本 页码`），但条目之间的换行被替换成了空格。

**根因定位**（已确认 `format_blocks` 在 `split_translated_result` 之后调用，[services/translation_content.py:140-150](file:///Users/chunju/work/pdfTrans/services/translation_content.py)）：

换行丢失的起点在**翻译主流程**，不是 `format_blocks`：

1. 目录页经 OCR / 语义合并后，以少量大块形式存在（每个块内含多行目录，用 `\n` 分隔）。
2. 翻译主流程的 `_generate_system_prompt`（[modules/translator.py:311](file:///Users/chunju/work/pdfTrans/modules/translator.py)）第 11 条"列表格式保持"只覆盖"项目符号如•、-、数字编号"，**没有覆盖目录（条目+页码的多行结构）**。LLM 不认为目录是"列表"，翻译时把目录多行合并成连续段落，`\n` 在翻译阶段就丢了。
3. `split_translated_result` 按文本长度比例切分翻译结果（[utils/text_processing.py:510-514](file:///Users/chunju/work/pdfTrans/utils/text_processing.py)），此时文本已无换行，切出的块也是连续段落。
4. `format_blocks` 在翻译之后运行，无法恢复已丢失的换行；且 `_FORMAT_SYSTEM_PROMPT` 缺乏对有意义换行的保护，可能进一步清理残留换行（实测 app.log 中翻译阶段保留了 `x \n| \n目录` 的换行，但 format_blocks 把它合并为 `x | 目录`）。

**代码状态更新**（2026-06-27）：`_FORMAT_SYSTEM_PROMPT` 已被 `fix-format-blocks-llm-dropping-markers` spec 重写为简化版本（[modules/translator.py:8-36](file:///Users/chunju/work/pdfTrans/modules/translator.py)），原规则 1-4（标点规范、中英文混排间距、多余空白清理、异常内容清理）已不存在，当前只有"输出格式要求"+"严格规则"两段。因此本 spec 不再涉及移除硬编码语言（原 Task 2.1/2.2）和收紧规则 3（原 Task 2.4），聚焦于**新增结构保留规则**。

## What Changes

- **核心修复**：修改 `_generate_system_prompt` 第 11 条，明确覆盖"目录"（条目+页码的多行结构）及其它多行结构化文本，要求翻译时保留逐行换行，不合并为连续段落。措辞语言无关。
- **二次保护**：修改 `_FORMAT_SYSTEM_PROMPT`，在"严格规则"区块新增"结构保留"规则：保留目录、列表、多行结构化文本的逐行换行，不得将换行替换为空格或合并行。识别目录模式（条目+页码、序号. 条目 页码、含前导点号的目录行）并逐行保留。
- 不改动 `format_blocks` 方法逻辑、`_parse_format_result`、计数校验、流式调用（上一 spec 已修复的丢块问题保持不变）。
- 不改动 `split_translated_result` 的按长度切分逻辑（既有设计，改动风险大；通过翻译 prompt 保留换行从源头解决）。
- 不改动上游 OCR / 语义合并逻辑。

## Impact

- Affected specs: 与 `fix-format-blocks-llm-dropping-markers` 互补（前者修丢块，本次修排版换行质量）；与 `fix-format-blocks-timeout-retry` 互补（前者修超时）。
- Affected code:
  - [modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py) — `_generate_system_prompt` 第 11 条 + `_FORMAT_SYSTEM_PROMPT` 常量字符串
- 不影响翻译主流程的其它规则（核心原则、语义风格、代码/公式/缩写/URL 保留、禁止元注释）、OCR、PDF 生成。
- 子类（AipingTranslator / QianfanTranslator / SiliconFlowTranslator）继承同一 prompt，无需各自改动。

## ADDED Requirements

### Requirement: 翻译提示词保留目录与多行结构化文本的换行

`_generate_system_prompt` 第 11 条 SHALL 明确覆盖目录（条目+页码的多行结构）及其它多行结构化文本，要求翻译时保留逐行换行，不合并为连续段落。规则措辞 SHALL 语言无关，不限定具体语言。

#### Scenario: 目录块翻译保留换行
- **WHEN** 翻译输入包含多行目录条目（如"条目 页码\n条目 页码\n..."或"序号. 条目 页码\n..."）
- **THEN** 翻译结果保留每个目录条目独占一行
- **AND** 不将目录条目之间的换行替换为空格或合并为连续段落

#### Scenario: 其它多行结构化文本保留换行
- **WHEN** 翻译输入包含多行列表、多行标题、多行结构化文本
- **THEN** 翻译结果保留原有的行结构
- **AND** 不合并行为连续段落

### Requirement: 排版提示词保留结构化文本的换行

`_FORMAT_SYSTEM_PROMPT` SHALL 包含"结构保留"规则，保留目录、列表、多行结构化文本的逐行换行，不得将换行替换为空格或合并行。作为翻译阶段保留换行之后的二次保护。

#### Scenario: 排版保留目录换行
- **WHEN** 一个文本块包含多行目录条目（翻译后已保留换行）
- **THEN** format_blocks 排版后保留每个目录条目独占一行
- **AND** 不将换行替换为空格或合并行

#### Scenario: 排版保留页脚/页眉多行结构
- **WHEN** 一个文本块包含多行页脚/页眉结构（如 "页码 \n| \n章节名"）
- **THEN** format_blocks 排版后保留原有的多行结构
- **AND** 不将换行替换为空格或合并行

## MODIFIED Requirements

### Requirement: _generate_system_prompt 第 11 条

`_generate_system_prompt`（[modules/translator.py:315](file:///Users/chunju/work/pdfTrans/modules/translator.py)）第 11 条修改：

- 现状：`**列表格式保持**：原文中的列表格式（换行、项目符号如•、-、数字编号等），在翻译结果中保持，不将列表项合并为连续段落；`
- 修改为：明确覆盖**目录**（条目+页码的多行结构）及其它多行结构化文本，要求保留逐行换行。措辞语言无关。

### Requirement: _FORMAT_SYSTEM_PROMPT 严格规则

`_FORMAT_SYSTEM_PROMPT`（[modules/translator.py:8-36](file:///Users/chunju/work/pdfTrans/modules/translator.py)）的"严格规则"区块新增一条"结构保留"规则：

- 保留目录、列表、多行结构化文本的逐行换行
- 识别目录模式（条目+页码、序号. 条目 页码、含前导点号的目录行）并逐行保留
- 不得将结构化文本的换行替换为空格或合并多行为一行
- 保留原文的换行结构，不得擅自合并行或把换行改为空格

## REMOVED Requirements

无删除项。原 spec 中涉及移除 `_FORMAT_SYSTEM_PROMPT` 硬编码"中文/英文"语言的子任务（原 Task 2.1/2.2/2.4/2.6）已因 `fix-format-blocks-llm-dropping-markers` spec 重写 prompt 而自然消解，不再适用。
