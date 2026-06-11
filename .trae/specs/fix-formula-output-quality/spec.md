# 公式输出质量修复 Spec

## Why

公式识别输出存在三个问题：1）LaTeX 字符间多余空格（如 "S O T R"）；2）长公式被截断；3）所有生成器（PDF/Word/Markdown）都没有实现 LaTeX 渲染，公式仅作为纯文本输出，无法显示为公式样式。

## What Changes

- **添加 LaTeX 后处理**：清洗多余空格、合并连续空格、修复 `\mathrm{}` 内字母序列空格
- **公式检测分辨率提升**：公式识别管线强制使用 960 分辨率
- **PDF 公式渲染**：将 LaTeX 转换为图像后嵌入 PDF
- **Word 公式渲染**：将 LaTeX 转换为 Office Math ML (OMML) 格式
- **Markdown 公式包裹**：用 `$...$` / `$$...$$` 包裹公式文本

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`、`modules/pdf_generator.py`、`modules/docx_generator.py`、`modules/markdown_generator.py`
- 行为变更：公式在 PDF/Word/Markdown 中正确渲染为公式样式

## ADDED Requirements

### Requirement: LaTeX 后处理

系统 SHALL 在提取公式 LaTeX 文本后进行后处理清洗，包括：

1. 去除 LaTeX 命令间的多余空格（保留 `\quad`、`\,`、`\;`、`~` 等有意空格命令）
2. 合并连续多个空格为单个空格
3. 修复 `\mathrm{}`、`\text{}` 等文本模式内的字母序列空格（如 `\mathrm{S O T R}` → `\mathrm{SOTR}`）
4. 去除 `{` 和 `}` 前后的多余空格

#### Scenario: 清洗多余空格

- **WHEN** 公式识别输出 `"S O T R{=}\frac{f_{\mathrm{d}}\cdot\beta_{S t}\cdot"`
- **THEN** 后处理后输出 `"SOTR {=} \\frac{f_{\\mathrm{d}} \\cdot \\beta_{St} \\cdot"`

#### Scenario: 保留有意空格

- **WHEN** 公式识别输出 `"x \quad y"`
- **THEN** 后处理后保留 `"x \\quad y"`

### Requirement: 公式检测分辨率提升

系统 SHALL 对公式识别管线使用更大的 `text_det_limit_side_len`，不受 low/minimal 分级的 720 限制。

#### Scenario: 公式管线分辨率

- **WHEN** 创建启用公式识别的管线（use_formula=True）
- **THEN** `text_det_limit_side_len=960`，覆盖分级默认值

### Requirement: PDF 公式渲染

系统 SHALL 在 PDF 生成时，对 `is_formula=True` 的文本块将 LaTeX 渲染为图像后嵌入，而非作为纯文本插入。

#### Scenario: 公式块 PDF 渲染

- **WHEN** PDF 生成器遇到 `is_formula=True` 的文本块
- **THEN** 将 LaTeX 渲染为图像（使用 matplotlib 或类似库）
- **AND** 将图像嵌入到对应 bbox 位置

#### Scenario: 普通文本块 PDF 渲染

- **WHEN** PDF 生成器遇到 `is_formula=False` 的文本块
- **THEN** 保持当前行为，使用 `insert_textbox()` 插入纯文本

### Requirement: Word 公式渲染

系统 SHALL 在 Word 生成时，对 `is_formula=True` 的文本块将 LaTeX 转换为 Office Math ML (OMML) 格式。

#### Scenario: 公式块 Word 渲染

- **WHEN** Word 生成器遇到 `is_formula=True` 的文本块
- **THEN** 将 LaTeX 转换为 OMML 格式并插入

#### Scenario: 普通文本块 Word 渲染

- **WHEN** Word 生成器遇到 `is_formula=False` 的文本块
- **THEN** 保持当前行为，使用 `add_run()` 插入纯文本

### Requirement: Markdown 公式包裹

系统 SHALL 在 Markdown 生成时，对 `is_formula=True` 的文本块用 `$...$`（行内公式）或 `$$...$$`（独立行公式）包裹。

#### Scenario: 行内公式

- **WHEN** Markdown 生成器遇到 `is_formula=True` 的文本块
- **THEN** 输出 `$latex_text$`

#### Scenario: 普通文本块

- **WHEN** Markdown 生成器遇到 `is_formula=False` 的文本块
- **THEN** 保持当前行为

### Requirement: LaTeX 截断检测

系统 SHALL 检测公式 LaTeX 是否可能被截断，并在日志中标记。

#### Scenario: 检测截断特征

- **WHEN** 公式 LaTeX 末尾为不完整命令（如 `\cdot`、`\times`、`\frac` 后无参数）
- **THEN** 日志输出警告标记该公式可能被截断

## MODIFIED Requirements

### Requirement: _process_page_layout 公式提取

在路径 A（parsing_res_list）和路径 B（formula_res_list）的 LaTeX 提取后，添加后处理调用。

## REMOVED Requirements

（无移除的需求）
