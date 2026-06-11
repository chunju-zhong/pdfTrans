# 公式三端输出失败修复 Spec

## Why

最后一次 OCR 翻译（34-40页）中，38页和39页的公式在 PDF/Word/Markdown 三端均输出异常：
1. PDF 38页公式显示为截断的 LaTeX 文本，未渲染为公式图像
2. Word 公式 OMML 转换失败，降级为纯文本
3. Markdown 中公式 LaTeX 含语法错误，无法正确渲染

根因是 PaddleOCR 的 PP-FormulaNet_plus-S 模型输出的 LaTeX 存在结构性语法错误（花括号不匹配、命令拼写错误），而现有 `_clean_latex()` 只做空格规范化，无法修复此类错误，导致三端全部降级为纯文本输出。

## What Changes

- **添加 LaTeX 语法修复**：在 `_clean_latex()` 中增加花括号匹配修复和常见命令拼写纠错
- **PDF 公式降级优化**：当 LaTeX 渲染失败时，尝试修复后重试，而非直接降级为纯文本
- **DOCX 公式降级优化**：当 latex2mathml 转换失败时，尝试修复 LaTeX 后重试
- **Markdown 公式验证**：输出前验证 LaTeX 语法，标记有问题的公式

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`（`_clean_latex` 方法）、`modules/pdf_generator.py`（公式渲染逻辑）、`modules/docx_generator.py`（OMML 转换逻辑）、`modules/markdown_generator.py`（公式输出逻辑）
- Affected specs: fix-formula-output-quality、fix-word-formula-omml-conversion、fix-md-formula-output

## 根因分析

### 参数影响分析

**日志显示 `det_side_len=720`，但实际传给 PPStructureV3 的是 960**：
- 第261行日志打印的是 `self.inference_params.get('text_det_limit_side_len', 960)` 的值，即系统分级（low）的 720
- 但第307-308行 `if use_formula: kwargs['text_det_limit_side_len'] = 960` 会覆盖为 960
- **日志有误导性**，实际公式检测分辨率并未被降低

**真正影响公式识别质量的是渲染 DPI**：
- 日志显示 `OCR 渲染 DPI: 100 (profiler=100, config=120)`
- 系统分级为 `low`（可用内存 5.4GB），profiler 将 DPI 从配置的 120 降为 100
- DPI 越低，渲染出的页面图像分辨率越低，公式细节越模糊，识别准确率越差
- 38页的复杂嵌套分式在 100 DPI 下细节丢失更严重，导致 PP-FormulaNet_plus-S 输出错误 LaTeX

**结论**：PP-FormulaNet_plus-S 模型本身可以正确识别公式，但在低 DPI 渲染条件下，复杂公式的识别准确率会显著下降。当前系统分级为 `low`，DPI 被降为 100，这是公式 LaTeX 质量差的间接原因。直接原因仍是模型输出了含语法错误的 LaTeX，而系统没有修复能力。

### 问题1：PDF 38页公式显示为文本

**日志证据**（第219-235行）：
```
公式渲染失败，降级为文本:
SOTR = \frac{f_{\mathrm{d}} \cdot \beta_{S_{\mathrm{f}}} \cdot C_{\mathrm{S},20} \cdot f_{\mathrm{S},\{it S}_}{,mathrm{S}}}{\alpha \cdot ...}
ParseSyntaxException: Expected {accent | symbol | function | ...}, found '}'  (at char 109), (line:1, col:110)
```

**根因链**：
1. PaddleOCR 输出 LaTeX 含语法错误：`f_{\mathrm{S},\{it S}_}{,mathrm{S}}` 中花括号不匹配
2. `_clean_latex()` 只做空格规范化，无法修复结构性错误
3. matplotlib 的 mathtext 解析器遇到语法错误抛出 `ParseSyntaxException`
4. PDF 生成器捕获异常，降级为纯文本
5. 纯文本 LaTeX 长达 342 字符，在 PDF 框中严重溢出，最终被截断到 105 字符（30%）

### 问题2：Word 公式 OMML 转换失败

**日志证据**（第298行）：
```
公式OMML转换失败，降级为文本:
```
（日志截断，但可确认 latex2mathml 转换失败）

**根因链**：
1. 同样的 LaTeX 语法错误导致 `latex2mathml` 转换失败
2. DOCX 生成器捕获异常，降级为纯文本

### 问题3：Markdown 中公式丢失/语法错误

**日志证据**（第102行）：
```
[FONT_DEBUG] page=39, label=text, is_body=True, text='$\\ mathtt\\ B B{\\ }\\mathtt B$'
```

**根因链**：
1. PaddleOCR 将公式误识别为普通文本（label=text），而非 formula
2. 该块 `is_formula=False`，Markdown 生成器不会用 `$...$` 包裹
3. 即使被检测为 formula，LaTeX 本身含语法错误（`\\ mathtt\\ B B{\\ }\\mathtt B`），Markdown 渲染器也无法正确显示

### 39页额外问题

39页有两个公式相关块：
- `formula: 1` — 被 OCR 检测为公式，但 LaTeX 为 `$TBC \mathsf{OD}_{\mathrm{{sin}}}}$`，末尾多一个 `}` 导致花括号不匹配
- `text: 1` — 内容为 `$\\ mathtt\\ B B{\\ }\\mathtt B$`，本应是公式但被版面分析标记为 text

## ADDED Requirements

### Requirement: LaTeX 花括号匹配修复

系统 SHALL 在 `_clean_latex()` 中增加花括号匹配修复逻辑：

1. 统计 `{` 和 `}` 数量，若不匹配则尝试修复
2. 对于多余的 `}`，从末尾向前移除多余的闭合花括号
3. 对于缺少的 `}`，在最近的未闭合 `{` 后补充闭合花括号
4. 修复后验证 LaTeX 是否可被 matplotlib 或 latex2mathml 解析

#### Scenario: 修复多余闭合花括号

- **WHEN** LaTeX 为 `$TBC \mathsf{OD}_{\mathrm{{sin}}}}$`（末尾多一个 `}`）
- **THEN** 修复后为 `$TBC \mathsf{OD}_{\mathrm{{sin}}}$`

#### Scenario: 修复嵌套不匹配

- **WHEN** LaTeX 含 `f_{\mathrm{S},\{it S}_}{,mathrm{S}}`（花括号严重不匹配）
- **THEN** 尝试修复为合法 LaTeX，若无法修复则标记为低置信度

### Requirement: LaTeX 常见命令拼写纠错

系统 SHALL 在 `_clean_latex()` 中增加常见 OCR 误识别模式的纠错：

1. `\{it ...}` → `\mathit{...}`（OCR 将 `\mathit` 误识别为 `\{it`）
2. `,mathrm` → `\mathrm`（OCR 丢失反斜杠）
3. `\\ mathtt\\` → `\mathtt`（多余空格和反斜杠）
4. `{\\ }` → ` `（强制空格在非必要上下文中移除）

#### Scenario: 修复 \mathit 误识别

- **WHEN** LaTeX 含 `\{it S}`
- **THEN** 修复为 `\mathit{S}`

#### Scenario: 修复丢失的反斜杠

- **WHEN** LaTeX 含 `,mathrm{S}`
- **THEN** 修复为 `\mathrm{S}`

### Requirement: PDF 公式渲染重试机制

系统 SHALL 在 PDF 公式渲染失败时，尝试修复 LaTeX 后重新渲染：

1. 首次渲染失败后，调用 `_clean_latex()` 的修复模式重新清洗
2. 修复后重试 matplotlib 渲染
3. 若仍失败，降级为纯文本并在日志中标记公式质量为"低置信度"

#### Scenario: 修复后渲染成功

- **WHEN** 原始 LaTeX 渲染失败，修复后 LaTeX 可被 matplotlib 解析
- **THEN** 使用修复后的 LaTeX 渲染公式图像

#### Scenario: 修复后仍失败

- **WHEN** 修复后 LaTeX 仍无法被 matplotlib 解析
- **THEN** 降级为纯文本，日志输出 WARNING 标记公式质量低

### Requirement: DOCX 公式转换重试机制

系统 SHALL 在 DOCX 公式 OMML 转换失败时，尝试修复 LaTeX 后重新转换：

1. 首次转换失败后，调用 LaTeX 修复逻辑
2. 修复后重试 latex2mathml 转换
3. 若仍失败，降级为纯文本

#### Scenario: 修复后 OMML 转换成功

- **WHEN** 原始 LaTeX 转换失败，修复后可被 latex2mathml 解析
- **THEN** 使用修复后的 LaTeX 转换为 OMML

### Requirement: Markdown 公式语法验证

系统 SHALL 在 Markdown 输出公式前验证 LaTeX 语法：

1. 对 `is_formula=True` 的块，验证 LaTeX 花括号匹配
2. 若语法有误，尝试修复后输出
3. 若无法修复，在公式前添加 HTML 注释标记 `<!-- formula-quality:low -->`

#### Scenario: 验证通过

- **WHEN** 公式 LaTeX 语法正确
- **THEN** 正常输出 `$$...$$` 或 `$...$`

#### Scenario: 验证失败但可修复

- **WHEN** 公式 LaTeX 花括号不匹配但可自动修复
- **THEN** 输出修复后的公式

## MODIFIED Requirements

### Requirement: _clean_latex 方法增强

`_clean_latex()` 方法 SHALL 在现有空格规范化逻辑之后，增加以下修复步骤：
1. 花括号匹配修复
2. 常见命令拼写纠错
3. 返回修复后的 LaTeX 和修复置信度标记

## REMOVED Requirements

（无移除的需求）
