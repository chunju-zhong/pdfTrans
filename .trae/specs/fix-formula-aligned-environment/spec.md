# 修复 \begin{aligned} 公式无法正确渲染 Spec

## Why

包含 `\begin{aligned}...\end{aligned}` 环境的 LaTeX 公式在 PDF 输出中无法正确显示，降级为纯文本。有两个根因：1）系统已安装 LaTeX（`/Library/TeX/texbin/latex`），但不在 PATH 中，`_check_latex_available()` 检测失败，usetex 路径被跳过；2）`_preprocess_latex_for_mathtext()` 不处理 `\begin{...}`/`\end{...}` 环境，mathtext 降级路径也失败。

## What Changes

- **修复 `_check_latex_available()` 的 LaTeX 检测路径**：增加 macOS 常见 LaTeX 安装路径的探测
- **在 `_preprocess_latex_for_mathtext()` 中增加 `\begin{aligned}` 环境转换**：将多行对齐公式转换为 mathtext 可渲染的单行格式
- **在 `_detect_formula()` 中增加 `\begin{...}` 环境检测**：识别以 `\begin{aligned}` 等环境开头的公式块

## Impact

- Affected code: `modules/pdf_generator.py`（`_check_latex_available`、`_preprocess_latex_for_mathtext` 方法）、`modules/ocr/llm_extractor.py`（`_detect_formula` 方法）
- Affected specs: fix-formula-latex-syntax-error、fix-formula-output-quality

## 根因分析

### 用户提供的公式示例

```
\begin{aligned}&=34+44+\left(3*23/ 3*2\right)\\&=34+44+\left(69/3*2\right)\\&=34+44+\left(23*2\right)\\&=34+44+46\end{aligned}
```

### 根因1：LaTeX 已安装但 PATH 检测失败（主因）

- macOS 上 MacTeX/TeX Live 安装 LaTeX 到 `/Library/TeX/texbin/latex`
- 但该路径不在当前进程的 PATH 环境变量中
- `_check_latex_available()` 使用 `subprocess.run(['latex', '--version'])` 检测，因 `latex` 不在 PATH 中返回 `False`
- **结果**：usetex 路径（Tier 1）被跳过，即使系统已安装完整 LaTeX 引擎
- **验证**：`/Library/TeX/texbin/latex --version` 返回 `pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026)`，LaTeX 完全可用

### 根因2：mathtext 降级路径不支持 `\begin{aligned}`

- `_preprocess_latex_for_mathtext()` 不处理 `\begin{...}`/`\end{...}` 环境
- matplotlib mathtext 解析器不支持 LaTeX 环境命令
- Tier 2（原始 mathtext）和 Tier 3（预处理后 mathtext）均失败
- 最终降级为纯文本

### 问题链

1. **`_check_latex_available()` 检测失败** → usetex 路径被跳过（这是最关键的，如果 usetex 正常工作，`\begin{aligned}` 可以直接渲染）
2. **`_detect_formula()` 不识别 `\begin{aligned}`** → 以 `\begin{aligned}` 开头的文本不会被标记为公式
3. **`_preprocess_latex_for_mathtext()` 不处理环境** → mathtext 降级路径也失败
4. **所有渲染路径失败** → 降级为纯文本，LaTeX 源码直接显示在 PDF 中

## ADDED Requirements

### Requirement: _check_latex_available 增加常见安装路径探测

系统 SHALL 在 `_check_latex_available()` 中增加对 macOS 常见 LaTeX 安装路径的探测：

1. 先尝试 PATH 中的 `latex`（现有逻辑）
2. 若 PATH 中未找到，依次探测以下路径：
   - `/Library/TeX/texbin/latex`（MacTeX 默认安装路径）
   - `/usr/local/texlive/2026/bin/universal-darwin/latex`（TeX Live 2026）
   - `/usr/local/texlive/2025/bin/universal-darwin/latex`（TeX Live 2025）
   - `/opt/homebrew/bin/latex`（Homebrew 安装）
3. 若在非 PATH 路径找到 LaTeX，将其目录加入 PATH 环境变量（或记录路径供 usetex 使用）
4. 缓存检测结果（现有逻辑已实现）

#### Scenario: LaTeX 在 MacTeX 默认路径

- **WHEN** LaTeX 安装在 `/Library/TeX/texbin/latex`，但不在 PATH 中
- **THEN** `_check_latex_available()` 返回 `True`，后续 usetex 渲染可用

#### Scenario: LaTeX 在 PATH 中

- **WHEN** `latex` 命令在 PATH 中可用
- **THEN** 行为与现有逻辑一致，返回 `True`

#### Scenario: LaTeX 未安装

- **WHEN** 所有探测路径均未找到 LaTeX
- **THEN** 返回 `False`，降级为 mathtext 渲染

### Requirement: _preprocess_latex_for_mathtext 增加 aligned 环境转换

系统 SHALL 在 `_preprocess_latex_for_mathtext()` 中增加对 `\begin{aligned}...\end{aligned}` 环境的转换处理：

1. 检测 `\begin{aligned}...\end{aligned}` 包装
2. 去除 `\begin{aligned}` 和 `\end{aligned}` 标记
3. 将 `\\` 分隔的多行内容用空格连接为单行
4. 去除每行行首的 `&` 对齐标记
5. 对其他常见环境（`\begin{gathered}`、`\begin{cases}`）做类似处理

#### Scenario: aligned 环境转换

- **WHEN** LaTeX 为 `\begin{aligned}&=34+44+\left(3*23/3*2\right)\\&=34+44+\left(69/3*2\right)\\&=34+44+\left(23*2\right)\\&=34+44+46\end{aligned}`
- **THEN** 预处理后为 `= 34 + 44 + (3*23/3*2) = 34 + 44 + (69/3*2) = 34 + 44 + (23*2) = 34 + 44 + 46`（`\left`/`\right` 已被现有逻辑去除）

#### Scenario: 带编号的 aligned

- **WHEN** LaTeX 为 `\begin{aligned}x &= 1 \\ y &= 2\end{aligned}`
- **THEN** 预处理后为 `x = 1 y = 2`

### Requirement: _detect_formula 增加 \begin 环境检测

系统 SHALL 在 `_detect_formula()` 中增加对以 `\begin{...}` 开头的 LaTeX 环境的检测：

1. 检测文本是否以 `\begin{aligned}`、`\begin{gathered}`、`\begin{cases}`、`\begin{equation}`、`\begin{equation*}`、`\begin{align}`、`\begin{align*}` 等数学环境开头
2. 若匹配，返回 `(True, 去除环境标记后的内容)`

#### Scenario: 检测 aligned 环境

- **WHEN** 文本为 `\begin{aligned}&=34+44+46\end{aligned}`
- **THEN** 返回 `(True, "&=34+44+46")`

#### Scenario: 检测 equation 环境

- **WHEN** 文本为 `\begin{equation}E=mc^2\end{equation}`
- **THEN** 返回 `(True, "E=mc^2")`

#### Scenario: 非公式环境不误判

- **WHEN** 文本为 `\begin{figure}图片\end{figure}`
- **THEN** 返回 `(False, 原文本)`

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
