# 修复 OCR 公式识别中乘法符号 `*` 被误识别为上标 `^{*}` Spec

## Why

PaddleOCR 的公式识别模型（PP-FormulaNet）在识别包含乘法符号 `*` 的公式时，可能将 `*` 误识别为上标 `^{*}`。例如原始公式 `0.6 * [...]` 被识别为 `0.6^{*}[...]`。

`latex2mathml` 将 `0.6^{*}` 正确解析为"`0.6` 的 `*` 次方"：
- LaTeX: `0.6^{*}` → MathML: `<msup><mn>0.6</mn><mo>*</mo></msup>`
- 在 OMML 中表现为 `<m:sSup>` 结构，`0.6` 作为底数被渲染为较小的脚本基准字

这导致：
1. **DOCX 中常数不可见**：`0.6`、`0.72`、`1.33` 等常数在 `<m:sSup>` 底数位置渲染时因字体/大小问题不可见
2. **语义错误**：`0.6^{*}` 表示"0.6 的 * 次方"，而实际应为乘法 `0.6 * [...]`

## What Changes

在 `_clean_latex` 中增加后处理规则，检测并修复 OCR 误识别的 `^{*}` 模式：

1. **数字后跟 `^{*}`**：`\d+\.?\d*\^{*}` → 替换的 `*` 为 `\cdot`（乘法点），因为 `\cdot` 在 LaTeX/MathML/OMML 中都是行内运算符，不会产生 `<msup>` 结构
2. **字母/变量后跟 `^{*}`**：保持不变（如 `x^{*}` 是合法的上标星号）

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`（`_clean_latex` 方法）
- 行为变更：OCR 输出的公式 LaTeX 中，数字后面的 `^{*}` 被修正为 `\cdot`，避免生成 `<msup>` 结构

## ADDED Requirements

### Requirement: `_clean_latex` 修复数字后 `^{*}` 误识别

系统 SHALL 在公式 LaTeX 清洗阶段，将数字后跟 `^{*}` 的模式替换为 `\cdot`（乘法点）。

#### Scenario: 整数后跟 `^{*}`

- **WHEN** LaTeX 包含 `0.6^{*}[...]`
- **THEN** 替换为 `0.6 \cdot [...]`

#### Scenario: 小数后跟 `^{*}`

- **WHEN** LaTeX 包含 `0.72^{*}F`
- **THEN** 替换为 `0.72 \cdot F`

#### Scenario: 变量后跟 `^{*}`（不应修改）

- **WHEN** LaTeX 包含 `x^{*}` 或 `a^{*}`
- **THEN** 保持不变

#### Scenario: 括号后跟 `^{*}`（不应修改）

- **WHEN** LaTeX 包含 `(...)^{*}`
- **THEN** 保持不变

#### Scenario: 正常乘法已使用 `\cdot`

- **WHEN** LaTeX 包含 `0.6 \cdot [...]`
- **THEN** 保持不变（无 `^{*}` 模式）

## MODIFIED Requirements

### Requirement: `_clean_latex` 增加 OCR 误识别修复

在 `_clean_latex` 方法末尾，在 `return result` 之前添加：

```python
# 修复 OCR 误识别：数字后面的乘法符号 * 被误识别为上标 ^{*}
# 例如: 0.6^{*} -> 0.6 \cdot, 0.72^{*}F -> 0.72 \cdot F
# 仅匹配数字后跟 ^{...} 且内容为 * 的情况
result = re.sub(r'(\d+\.?\d*)\^{\{\*\}\}', r'\1 \\cdot', result)
```

## REMOVED Requirements

无