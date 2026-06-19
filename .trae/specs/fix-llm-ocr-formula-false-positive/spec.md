# 修复 LLM OCR 公式检测：英文单词区分法 Spec

## Why

移除高 LaTeX 密度检测后，纯公式文本（如 `\mathrm{Q}_{\mathrm{d}} = 1000\mathrm{m}^3 /\mathrm{d}`）不再被检测为公式，进入翻译流程后翻译器无法正确处理 LaTeX，导致公式显示为原始 LaTeX 文本。

需要一种更精确的检测方式：区分"纯公式"和"包含英文说明的混合文本"。

## What Changes

- **添加"无英文单词"检测规则**：在定界符检测之后，增加一条规则——如果文本不包含英文单词（连续3个及以上英文字母），且包含 LaTeX 命令（`\command` 格式），则标记为纯公式
- **保留定界符包裹检测**：`$...$`、`$$...$$`、`\(...\)`、`\[...\]` 包裹的文本仍优先检测

## Impact

- Affected code: `modules/ocr/llm_extractor.py`（`_detect_formula` 方法）
- Affected specs: `fix-llm-ocr-formula-false-positive`（替换高密度检测为英文单词检测）

## ADDED Requirements

### Requirement: 无英文单词的 LaTeX 文本检测为公式

`_detect_formula` SHALL 在定界符检测之后，增加"无英文单词"检测规则：

条件（全部满足）：
1. 文本不包含连续3个及以上英文字母组成的单词（排除 LaTeX 命令中的字母如 `\mathrm`）
2. 文本包含至少一个 LaTeX 命令（`\command{...}` 格式）
3. 文本不包含 CJK 字符或全角标点

理由：纯公式文本（如 `\mathrm{Q}_{\mathrm{d}} = 1000\mathrm{m}^3 /\mathrm{d}`）不包含英文单词，只有数学符号、数字和 LaTeX 命令。而混合文本（如 `High rate: \(15 - 30gBOD_5 / m^2 d\)`）包含 "High"、"rate" 等英文单词。

#### Scenario: 无英文单词的纯公式被检测为公式

- **WHEN** 文本为 `\mathrm{Q}_{\mathrm{d}} = 1000\mathrm{m}^3 /\mathrm{d}`
- **THEN** `is_formula = True`（无英文单词，有 LaTeX 命令）

#### Scenario: 无英文单词的公式+标签被检测为公式

- **WHEN** 文本为 `\mathrm{A}_{\mathrm{MBBR}}\) : \(1000^{*}200*1,06^{0.94}\)`
- **THEN** `is_formula = True`（无英文单词，有 LaTeX 命令）

#### Scenario: 包含英文单词的混合文本不标记为公式

- **WHEN** 文本为 `High rate: \(15 - 30\mathrm{gBOD}_5 / \mathrm{m}^2 \mathrm{d}\) Normal rate : \(8 - 12\mathrm{gBOD}_5 / \mathrm{m}^2 \mathrm{d}\)`
- **THEN** `is_formula = False`（包含 "High"、"rate"、"Normal" 等英文单词）

#### Scenario: 包含英文单词的公式+说明不标记为公式

- **WHEN** 文本为 `Loading rate : \(\mathrm{LR}_{\mathrm{BOD}} = Q_{\mathrm{d}} \cdot \mathrm{BOD}_{\mathrm{in}}\)`
- **THEN** `is_formula = False`（包含 "Loading"、"rate" 等英文单词）

#### Scenario: 包含中文的文本不标记为公式

- **WHEN** 文本为 `当 \(T = 5 - 10^{\circ}C\)`
- **THEN** `is_formula = False`（包含 CJK 字符）

## MODIFIED Requirements

### Requirement: _detect_formula 检测规则

定界符包裹检测 + 无英文单词检测（替代高 LaTeX 密度检测）。

## REMOVED Requirements

### Requirement: 高 LaTeX 密度检测

**Reason**: 30% 阈值导致大量误判，"无英文单词"检测更精确。
**Migration**: 使用"无英文单词 + 有 LaTeX 命令"规则替代。
