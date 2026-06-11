# 修复 Markdown 输出公式显示不正确 Spec

## Why

Markdown 输出时，公式文本虽然被 `$...$` 包裹，但随后整个文本被发送给 LLM 做布局格式化。LLM 的系统提示词中完全没有公式保护指令，导致 LLM 可能剥离 `$` 标记、转义 `$` 符号、拆分公式内容或将其当作普通文本重新排版，最终公式在 Markdown 中显示不正确。

## What Changes

- **在布局格式化系统提示词中增加公式保护规则**：明确要求 LLM 保留 `$...$` 和 `$$...$$` 公式标记，不修改公式内容
- **区分行内公式与独立行公式**：根据公式块的 bbox 宽度占比判断是行内公式还是独立行公式，分别使用 `$...$` 和 `$$...$$` 包裹

## Impact

- Affected code: `modules/markdown_generator.py` 的 `_load_layout_prompt()` 和公式包裹逻辑
- 行为变更：Markdown 输出中公式标记被 LLM 完整保留，不再被破坏

## ADDED Requirements

### Requirement: 布局格式化提示词公式保护

系统 SHALL 在 `_load_layout_prompt()` 的系统提示词中增加公式保护规则，明确要求 LLM：

1. 不修改、删除或转义 `$...$`（行内公式）和 `$$...$$`（独立行公式）标记
2. 公式内容（LaTeX 表达式）必须原样保留，不添加空格、换行或解释
3. 不将公式内容加粗、斜体或其他格式化

#### Scenario: LLM 保留行内公式标记

- **WHEN** 输入文本包含 `$E=mc^2$`
- **THEN** LLM 输出中保留 `$E=mc^2$`，不剥离 `$`、不转义为 `\$`、不修改公式内容

#### Scenario: LLM 保留独立行公式标记

- **WHEN** 输入文本包含 `$$\frac{a}{b}$$`
- **THEN** LLM 输出中保留 `$$\frac{a}{b}$$`，不修改公式内容

### Requirement: 区分行内公式与独立行公式

系统 SHALL 根据公式块的布局特征区分行内公式和独立行公式：

1. 独立行公式（公式块宽度占页面宽度比例 ≥ 60%）：使用 `$$...$$` 包裹
2. 行内公式（公式块宽度占页面宽度比例 < 60%）：使用 `$...$` 包裹

#### Scenario: 独立行公式使用 `$$...$$`

- **WHEN** 公式块 bbox 宽度占页面宽度 ≥ 60%
- **THEN** 输出 `$$latex_text$$`

#### Scenario: 行内公式使用 `$...$`

- **WHEN** 公式块 bbox 宽度占页面宽度 < 60%
- **THEN** 输出 `$latex_text$`

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
