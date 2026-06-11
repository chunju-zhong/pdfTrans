# 修复38页Word输出公式显示问题 Spec

## Why

38页公式在 Word 输出中无法正常显示。日志显示 `公式OMML转换失败，降级为文本: Opening and ending tag mismatch: e line 1 and sub`。根因是 `_mathml_to_omml` 方法使用简单字符串替换将 MathML 转换为 OMML，导致 XML 标签不匹配，`etree.fromstring` 解析失败，公式降级为纯 LaTeX 文本。

## What Changes

- **重写 `_mathml_to_omml` 方法**：使用 lxml 的树形解析和递归转换替代简单字符串替换，正确处理 MathML 到 OMML 的结构映射
- **处理 MathML 子元素边界**：正确区分 `<msub>`/`<msup>`/`<msubsup>` 的 base/sub/sup 部分，以及 `<mfrac>` 的 numerator/denominator 部分

## Impact

- Affected code: `modules/docx_generator.py` 的 `_mathml_to_omml` 方法和 `_insert_formula_omml` 方法
- 行为变更：公式在 Word 中正确显示为 OMML 公式对象，而非降级为 LaTeX 文本

## ADDED Requirements

### Requirement: MathML 到 OMML 的正确结构转换

系统 SHALL 使用树形解析方式将 MathML 转换为 OMML，正确处理子元素边界。

#### Scenario: 简单下标公式

- **WHEN** LaTeX 公式包含下标（如 `SOTR_{d}`）
- **THEN** MathML `<msub><mi>SOTR</mi><mi>d</mi></msub>` 被正确转换为 `<m:sSub><m:e><m:r><m:t>SOTR</m:t></m:r></m:e><m:sub><m:r><m:t>d</m:t></m:r></m:sub></m:sSub>`

#### Scenario: 分数公式

- **WHEN** LaTeX 公式包含分数（如 `\frac{a}{b}`）
- **THEN** MathML `<mfrac><mi>a</mi><mi>b</mi></mfrac>` 被正确转换为 `<m:f><m:fPr><m:ctrlPr/></m:fPr><m:num><m:r><m:t>a</m:t></m:r></m:num><m:den><m:r><m:t>b</m:t></m:r></m:den></m:f>`

#### Scenario: 复杂嵌套公式

- **WHEN** LaTeX 公式包含嵌套结构（如 `SOTR = \frac{f_{d} \cdot \alpha \cdot \beta \cdot C_{\infty}}{...}`）
- **THEN** 转换后的 OMML XML 结构完整，标签正确匹配，`etree.fromstring` 解析成功

#### Scenario: 不支持的 MathML 元素

- **WHEN** 遇到未处理的 MathML 元素（如 `<mover>`、`<munder>`、`<msqrt>` 等）
- **THEN** 递归处理子元素，将未识别的元素内容作为普通文本输出

## MODIFIED Requirements

### Requirement: _mathml_to_omml 方法

`_mathml_to_omml` SHALL 使用 lxml 树形解析和递归转换，而非简单字符串替换。

## REMOVED Requirements

（无移除的需求）

## 根因分析

### 问题：38页 Word 输出公式不显示

**日志证据**：
```
公式OMML转换失败，降级为文本: Opening and ending tag mismatch: e line 1 and sub, line 1, column 328
```

**根因**：`_mathml_to_omml` 使用简单字符串替换，无法正确处理 MathML 子元素边界。

具体 bug 示例：

1. **`<msub>` 转换**：
   - 输入：`<msub><mi>SOTR</mi><mi>d</mi></msub>`
   - 当前输出：`<m:sSub><m:e>SOTR</m:sub></m:sSub>` — **`<m:e>` 没有 `</m:e>`，直接跳到 `</m:sub>`**
   - 正确输出：`<m:sSub><m:e><m:r><m:t>SOTR</m:t></m:r></m:e><m:sub><m:r><m:t>d</m:t></m:r></m:sub></m:sSub>`

2. **`<mfrac>` 转换**：
   - 输入：`<mfrac><mrow>num</mrow><mrow>den</mrow></mfrac>`
   - 当前输出：`<m:f><m:fPr>...</m:fPr><m:num>numden</m:den></m:f>` — **缺少 `</m:num><m:den>`**
   - 正确输出：`<m:f><m:fPr>...</m:fPr><m:num>num</m:num><m:den>den</m:den></m:f>`

3. **`<mstyle>` 正则替换**：
   - `omml.replace('<mstyle[^>]*>', '')` — `str.replace` 不支持正则，需要用 `re.sub`

**修改方案**：重写 `_mathml_to_omml`，使用 lxml 解析 MathML 为树结构，递归遍历节点并生成正确的 OMML XML。
