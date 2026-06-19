# LLM OCR 公式检测与标记 Spec

## Why

LLM OCR 提取器（DeepSeek-OCR）没有公式检测逻辑，返回的 LaTeX 公式文本（如 `$Q_{d} = 1000\mathrm{m}^3 /\mathrm{d}$`）被当作普通文本处理，导致两个问题：
1. **翻译风险**：公式文本进入翻译流程，仅靠翻译 prompt 第12条规则兜底保护，翻译器仍可能修改 LaTeX 内容
2. **渲染问题**：PDF 渲染时公式作为纯文本输出（如 `$Q_{d} = 1000\mathrm{m}^3 /\mathrm{d}$`），而非用 matplotlib 渲染为数学公式图片，导致 PDF 中显示原始 LaTeX 代码而非排版后的公式

PaddleOCR 提取器有完整的公式检测机制（`is_formula=True` 标记 + matplotlib 渲染 + 翻译跳过），LLM OCR 提取器需要同样的能力。

## What Changes

- 在 `llm_extractor.py` 的 `_parse_ref_tags_response` 和 `_parse_json_response` 中添加公式检测逻辑，识别包含 LaTeX 语法的文本块并标记 `is_formula=True`
- 公式检测规则：文本中包含 `$...$` 或 `$$...$$` 或 `\(...\)` 或 `\[...\]` 包裹的 LaTeX 内容

## Impact

- Affected code: `modules/ocr/llm_extractor.py`
- Affected specs: `fix-llm-ocr-font-size-and-rendering`（公式块的字体大小估算可能需要调整）
- 下游受益：`translation_service.py`（公式块自动跳过翻译）、`pdf_generator.py`（公式块用 matplotlib 渲染为图片）、`docx_generator.py`（公式块用 OMML 渲染）、`markdown_generator.py`（公式块用 `$...$` 标记）

## ADDED Requirements

### Requirement: LLM OCR 公式检测与标记

LLM OCR 提取器 SHALL 检测文本块中包含的 LaTeX 公式，并将包含公式的文本块标记为 `is_formula=True`。

检测规则（满足任一条件即标记为公式）：
1. 文本以 `$` 开头和结尾（行内公式），如 `$Q_{d} = 1000\mathrm{m}^3 /\mathrm{d}$`
2. 文本以 `$$` 开头和结尾（独立行公式），如 `$$\mathrm{k}_{\mathrm{T}} = 1,07(\mathrm{T}^{- 10})$$`
3. 文本以 `\(` 开头和 `\)` 结尾（LaTeX 行内公式）
4. 文本以 `\[` 开头和 `\]` 结尾（LaTeX 独立行公式）
5. 文本**整体**被上述任一格式包裹（即整个文本块就是一个公式）

注意：仅当文本**整体**是公式时才标记。如果文本是"负荷率：$\mathrm{LR}_{\mathrm{BOD}} = ...$"这种混合格式（中文说明文字 + 公式），**不**标记为公式，因为这种混合文本需要翻译中文部分，公式部分由翻译 prompt 保护。

#### Scenario: 纯公式文本块标记

- **WHEN** DeepSeek-OCR 返回文本 `$Q_{d} = 1000\mathrm{m}^3 /\mathrm{d}$`
- **THEN** 该文本块 `is_formula = True`

#### Scenario: 纯 LaTeX 行内公式标记

- **WHEN** DeepSeek-OCR 返回文本 `\(\mathrm{k}_{\mathrm{T}} = 1,07(\mathrm{T}^{- 10})\)`
- **THEN** 该文本块 `is_formula = True`

#### Scenario: 混合文本不标记为公式

- **WHEN** DeepSeek-OCR 返回文本 `高负荷率：$15 - 30\mathrm{gBOD}_5 / \mathrm{m}^2 \mathrm{d}$`
- **THEN** 该文本块 `is_formula = False`（因为包含中文说明文字，需要翻译）

#### Scenario: 多公式混合文本不标记

- **WHEN** DeepSeek-OCR 返回文本 `$\mathrm{Q}_{\mathrm{d}} = 1000\mathrm{m}^3 /\mathrm{d}$，$\mathrm{BOD}_{\mathrm{in}} = 200\mathrm{g / m}^3$，$T = 18^{\circ}\mathrm{C}$，Carrier selected (K3)：$500\mathrm{m}^2 /\mathrm{m}^3$ Filling fraction $\alpha$：0,6（60%）Design loading rate $\mathrm{LR}_{\mathrm{BOD}}$：$10\mathrm{gBOD} / \mathrm{m}^2 \mathrm{d}$`
- **THEN** 该文本块 `is_formula = False`（混合了多个公式和说明文字，需要翻译说明文字部分）

#### Scenario: 纯独立行公式标记

- **WHEN** DeepSeek-OCR 返回文本 `$$\mathrm{k}_{\mathrm{T}} = 1,07(\mathrm{T}^{- 10})$$`
- **THEN** 该文本块 `is_formula = True`

#### Scenario: 普通文本不标记

- **WHEN** DeepSeek-OCR 返回文本 `BOD/COD-removal dimensioning is based on loading rate`
- **THEN** 该文本块 `is_formula = False`

### Requirement: 公式块 LaTeX 清理

当文本块被标记为 `is_formula=True` 时，SHALL 去除包裹公式的定界符（`$...$`、`$$...$$`、`\(...\)`、`\[...\]`），仅保留纯 LaTeX 内容存入 `block_text`。这与 PaddleOCR 提取器的 `_clean_latex` 方法行为一致，确保下游渲染逻辑（matplotlib、OMML）能正确处理。

#### Scenario: 去除 `$...$` 定界符

- **WHEN** 文本为 `$Q_{d} = 1000\mathrm{m}^3 /\mathrm{d}$`
- **THEN** `block_text` = `Q_{d} = 1000\mathrm{m}^3 /\mathrm{d}`

#### Scenario: 去除 `$$...$$` 定界符

- **WHEN** 文本为 `$$\mathrm{k}_{\mathrm{T}} = 1,07(\mathrm{T}^{- 10})$$`
- **THEN** `block_text` = `\mathrm{k}_{\mathrm{T}} = 1,07(\mathrm{T}^{- 10})`

#### Scenario: 去除 `\(...\)` 定界符

- **WHEN** 文本为 `\(\mathrm{m}^2 /\mathrm{m}^3\)`
- **THEN** `block_text` = `\mathrm{m}^2 /\mathrm{m}^3`

## MODIFIED Requirements

### Requirement: LLM OCR 文本块创建（原 fix-llm-ocr-coord-and-text）

在 `_parse_ref_tags_response` 和 `_parse_json_response` 中创建 TextBlock 后，增加公式检测和标记步骤。如果文本被识别为纯公式，设置 `tb.is_formula = True` 并清理定界符。

## REMOVED Requirements

无
