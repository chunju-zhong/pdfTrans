# 修复 LLM OCR 公式渲染失败 Spec

## Why

DeepSeek-OCR 返回的 LaTeX 公式大量使用 `\text{}`、`\mathrm{}` 等命令，matplotlib 默认的 mathtext 解析器不支持这些命令，导致 `_render_formula_image` 渲染失败，公式降级为纯文本输出。用户看到的 PDF 中公式显示为原始 LaTeX 代码（如 `$15 - 30 \text{g BOD}_5 / \text{m}^2 \text{d}$`）而非排版后的数学公式。

## What Changes

- 在 `_render_formula_image` 中启用 `plt.rcParams['text.usetex'] = True`，使用系统 LaTeX 引擎渲染公式
- 添加 LaTeX 环境检测：首次调用时检测系统是否安装 LaTeX，缓存结果
- 添加降级策略：如果 usetex 不可用，预处理 LaTeX 去除 `\text{}`、`\mathrm{}` 等不支持的命令，尝试用 mathtext 渲染
- 在 LLM OCR 的 `_detect_formula` 中添加对"主要包含 LaTeX 命令"的文本块的检测（放宽检测规则）

## Impact

- Affected code: `modules/pdf_generator.py`（`_render_formula_image` 方法）、`modules/ocr/llm_extractor.py`（`_detect_formula` 方法）
- Affected specs: `fix-llm-ocr-formula-detection`（放宽检测规则）

## ADDED Requirements

### Requirement: 使用 usetex 渲染公式

`_render_formula_image` SHALL 优先使用 `plt.rcParams['text.usetex'] = True` 渲染 LaTeX 公式，以支持 `\text{}`、`\mathrm{}`、`\mathbf{}` 等高级 LaTeX 命令。

#### Scenario: 系统安装了 LaTeX

- **WHEN** 系统安装了 LaTeX（`latex` 命令可用）
- **THEN** `_render_formula_image` 使用 `usetex=True` 渲染公式
- **AND** 包含 `\text{g BOD}_5` 的公式能正确渲染为排版后的数学公式

#### Scenario: 系统未安装 LaTeX

- **WHEN** 系统未安装 LaTeX
- **THEN** 预处理 LaTeX 去除不支持的命令后用 mathtext 渲染
- **AND** 渲染失败时降级为纯文本

### Requirement: LaTeX 环境检测与缓存

系统 SHALL 在首次调用 `_render_formula_image` 时检测系统是否安装了 LaTeX（执行 `latex --version` 或尝试渲染测试公式），缓存结果避免重复检测。

#### Scenario: 首次渲染时检测

- **WHEN** 首次调用 `_render_formula_image`
- **THEN** 检测系统 LaTeX 可用性，缓存结果到类属性

#### Scenario: 后续渲染时使用缓存

- **WHEN** 后续调用 `_render_formula_image`
- **THEN** 直接使用缓存的检测结果，不再重复检测

### Requirement: mathtext 降级预处理

当 usetex 不可用时，SHALL 预处理 LaTeX 去除 mathtext 不支持的命令，尝试用 mathtext 渲染。预处理规则：
1. `\text{content}` → `content`（直接展开文本内容）
2. `\mathrm{content}` → `content`
3. `\mathbf{content}` → `content`
4. `\mathit{content}` → `content`
5. `\mathsf{content}` → `content`
6. `\mathtt{content}` → `content`
7. `\textbf{content}` → `content`

这与 PaddleOCR 的 `_clean_latex` 方法行为一致。

#### Scenario: 预处理后 mathtext 可渲染

- **WHEN** LaTeX 为 `\text{LR}_{\text{BOD}} = Q_{\mathrm{d}} \cdot \text{BOD}_{\mathrm{in}}`
- **AND** usetex 不可用
- **THEN** 预处理为 `LR_{BOD} = Q_{d} \cdot BOD_{in}`
- **AND** 用 mathtext 渲染

#### Scenario: 预处理后 mathtex 仍无法渲染

- **WHEN** 预处理后的 LaTeX 仍包含 mathtext 不支持的命令
- **THEN** 渲染失败，降级为纯文本输出

### Requirement: 放宽 LLM OCR 公式检测规则

当前 `_detect_formula` 仅检测"整体被定界符包裹"的纯公式文本。DeepSeek-OCR 返回的很多公式文本虽然被 `$...$` 包裹，但前后可能有空格或换行，导致检测失败。SHALL 放宽检测规则：

1. 去除首尾空白后再检测定界符
2. 添加"高 LaTeX 密度"检测：如果文本中 LaTeX 命令（以 `\` 开头的命令词）占比超过 30%，且不包含中文/日文/韩文字符，标记为公式

#### Scenario: 前后有空白仍检测为公式

- **WHEN** 文本为 `  $15 - 30 \text{g BOD}_5 / \text{m}^2 \text{d}$  `
- **THEN** 去除空白后检测到 `$...$`，标记为公式

#### Scenario: 高 LaTeX 密度文本检测为公式

- **WHEN** 文本为 `k_{\mathrm{T}} = 1,07(\mathrm{T}^{- 10})`（无定界符，但 LaTeX 命令密度高）
- **THEN** 标记为公式

#### Scenario: 包含中文的混合文本不标记

- **WHEN** 文本为 `当 $\mathrm{T} = 5 - 10^{\circ}\mathrm{C}$`
- **THEN** 不标记为公式（包含中文说明文字）

## MODIFIED Requirements

### Requirement: _render_formula_image 渲染逻辑

原逻辑：直接用 matplotlib mathtext 渲染，失败时降级为纯文本。
修改为：优先 usetex → 降级预处理+mathtext → 最终降级纯文本。

## REMOVED Requirements

无
