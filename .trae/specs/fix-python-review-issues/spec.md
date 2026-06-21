# 修复 Python 代码审查问题 Spec

## Why
Python 代码审查发现 5 个 HIGH、5 个 MEDIUM 和 2 个 LOW 级别问题，涉及 LaTeX 环境正则不匹配、线程安全、死代码、副作用隐含、跨平台路径等，需逐一修复以确保代码质量和正确性。

## What Changes
- 修复 `_preprocess_latex_for_mathtext` 中 `\begin`/`\end` 环境名不匹配的正则（使用反向引用）
- 修复 `_preprocess_latex_for_mathtext` 中兜底 `\\` 和 `&` 替换过于激进的问题
- 修复 `_check_latex_available` 中修改 `os.environ['PATH']` 的线程安全问题
- 移除 `llm_extractor.py` 中未使用的 `fix_line_break_hyphens` import（死代码）
- 在 `_compute_table_layout` 的 docstring 中标注修改 `matrix` 参数的副作用
- 修复 `_parse_html_table` 返回值检查不一致（`if cells:` → `if cells is not None:`）
- 扩展 `_estimate_text_display_width` 的 CJK 宽度估算范围（增加日文/韩文）
- 优化表格单元格截断循环（线性 → 二分查找）
- 收窄 `docx_generator.py` 合并单元格的异常捕获范围
- 修复 `llm_extractor.py` 模块级 import 顺序（常量与 import 交错）
- 扩展 `_check_latex_available` 的 LaTeX 路径探测支持 Linux 和 Windows

## Impact
- Affected code: `modules/pdf_generator.py`, `modules/ocr/llm_extractor.py`, `modules/docx_generator.py`, `utils/text_processing.py`

## ADDED Requirements

### Requirement: LaTeX 环境正则使用反向引用确保 begin/end 环境名一致
`_preprocess_latex_for_mathtext` 中的环境去除正则 SHALL 使用捕获组 + 反向引用，确保 `\begin{env1}` 和 `\end{env1}` 的环境名一致，避免 `\begin{aligned}...\end{cases}` 被错误匹配。

#### Scenario: 不同环境名的 begin/end 不被匹配
- **WHEN** 输入为 `\begin{aligned}...\end{cases}`
- **THEN** 正则不匹配，内容保持不变

#### Scenario: 相同环境名的 begin/end 被正确去除
- **WHEN** 输入为 `\begin{aligned}&=1\\\\&=2\end{aligned}`
- **THEN** 输出为 `=1 =2`（`\\` 替换为空格，`&` 去除）

### Requirement: 兜底 `\\` 和 `&` 替换仅在检测到残留模式时执行
`_preprocess_latex_for_mathtext` 中的兜底替换 SHALL 仅在输入中确实存在残留的 `\\` 行分隔符或 `&` 对齐标记时才执行，避免破坏合法内容。

### Requirement: LaTeX 检测的 PATH 修改需在锁内完成
`_check_latex_available` 中对 `os.environ['PATH']` 的修改 SHALL 在 `_latex_lock` 内完成，确保线程安全。

### Requirement: `_compute_table_layout` 标注副作用
`_compute_table_layout` 的 docstring SHALL 明确说明该方法会修改传入 `matrix` 参数中单元格的 `estimated_lines` 属性。

### Requirement: `_parse_html_table` 返回值使用 `is not None` 检查
调用方 SHALL 使用 `if cells is not None:` 而非 `if cells:` 来检查 `_parse_html_table` 的返回值，避免空矩阵被误判为 falsy。

### Requirement: CJK 宽度估算覆盖日文和韩文
`_estimate_text_display_width` SHALL 将日文平假名（\u3040-\u309F）、片假名（\u30A0-\u30FF）、韩文（\uAC00-\uD7AF）纳入全角宽度计算。

### Requirement: 表格单元格截断使用二分查找
表格单元格文本截断 SHALL 使用二分查找而非线性遍历，将 `insert_textbox` 调用次数从 O(n) 降至 O(log n)。

### Requirement: LaTeX 检测路径支持 Linux 和 Windows
`_check_latex_available` 的 fallback 路径探测 SHALL 包含 Linux 常见路径（`/usr/bin/latex`、`/usr/local/texlive/*/bin/x86_64-linux/latex`、`/usr/local/texlive/*/bin/aarch64-linux/latex`）和 Windows 常见路径（`C:/texlive/*/bin/windows/latex.exe`、`C:/Program Files/MiKTeX/miktex/bin/x64/latex.exe`），确保跨平台可用。

### Requirement: `llm_extractor.py` 模块级 import 顺序规范
`llm_extractor.py` 中常量 `TABLE_HTML_MARKER` 与 `import base64`/`import logging` 交错，SHALL 将所有 import 移到文件顶部，常量定义放在 import 之后。

## MODIFIED Requirements

### Requirement: LaTeX 环境去除正则
原正则 `r'\\begin\{' + env_names + r'\}(.*?)\\end\{' + env_names + r'\}'` 中 begin 和 end 的环境名独立匹配，修改为使用捕获组 + 反向引用 `r'\\begin\{(aligned|gathered|cases|equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}'`，确保环境名一致。

### Requirement: docx_generator 合并单元格异常捕获
将 `except Exception as e:` 收窄为 `except (ValueError, KeyError) as e:`，避免隐藏编程错误。

## REMOVED Requirements

### Requirement: 无
本次修改不删除任何现有功能。
