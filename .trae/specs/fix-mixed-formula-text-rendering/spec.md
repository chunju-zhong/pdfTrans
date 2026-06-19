# 修复混合公式文本渲染 Spec

## Why
LLM OCR 提取的文本中存在大量"中文前缀+LaTeX公式"的混合文本（如"高负荷率：$15 - 30\mathrm{gBOD}_5 / \mathrm{m}^2 \mathrm{d}$"），当前 `_detect_formula` 因含 CJK 字符将其判定为非公式，导致 LaTeX 语法被当作纯文本渲染。同时，纯公式文本在 mathtext 渲染失败时也降级为纯文本，LaTeX 命令直接显示。

## What Changes
- 修改 PDF 生成器：对 `is_formula=True` 的文本块，渲染失败时不降级为纯文本，而是先尝试预处理 LaTeX 后重新渲染
- 修改 PDF 生成器：对非公式文本块，检测文本中是否包含 LaTeX 公式片段（`$...$`、`\(...\)` 等），如有则将公式部分提取为图片渲染，非公式部分用文本渲染
- 增强 `_preprocess_latex_for_mathtext`：处理更多 mathtext 不支持的命令（`\circ`、`\cdot`、`\alpha` 等）

## Impact
- Affected specs: fix-llm-ocr-formula-usetex
- Affected code: modules/pdf_generator.py

## ADDED Requirements

### Requirement: 混合公式文本的公式片段提取渲染
系统 SHALL 对非公式文本块中嵌入的 LaTeX 公式片段（`$...$`、`$$...$$`、`\(...\)`、`\[...\]`）进行提取，将公式部分渲染为图片，非公式部分用文本渲染。

#### Scenario: 中文前缀+行内公式
- **WHEN** 翻译文本为 "高负荷率：$15 - 30\mathrm{gBOD}_5 / \mathrm{m}^2 \mathrm{d}$"
- **THEN** "高负荷率："用文本渲染，"$15 - 30\mathrm{gBOD}_5 / \mathrm{m}^2 \mathrm{d}$"渲染为公式图片

#### Scenario: 纯公式文本渲染失败
- **WHEN** `is_formula=True` 的文本块渲染失败
- **THEN** 先尝试预处理 LaTeX（去除不支持的命令）后重新渲染，而非直接降级为纯文本

### Requirement: mathtext 预处理增强
系统 SHALL 在 `_preprocess_latex_for_mathtext` 中处理更多 mathtext 不支持的命令：
- `\circ` → `°`
- `\cdot` → `·`
- `\alpha` → `α`
- `\beta` → `β`
- 其他常见希腊字母和数学符号

#### Scenario: 预处理后 mathtext 可渲染
- **WHEN** LaTeX 为 `k_{T} = 1,07(T^{- 10})` （已去除 \mathrm）
- **THEN** mathtext 成功渲染为公式图片
