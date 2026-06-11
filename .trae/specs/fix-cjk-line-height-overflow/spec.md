# 修复 CJK 字体行高大于拉丁字体导致翻译文本溢出 bbox Spec

## Why

中文翻译文本虽然行数比英文原文少（9行 vs 11行），但仍然溢出原始 bbox，被下一段落的白色背景遮挡。根因是 CJK 字体的行高（1.3-1.5x 字体大小）远大于拉丁字体的行高（1.15-1.2x 字体大小），当从拉丁字体切换到 CJK 字体时，每行占用的垂直空间增加 20-30%，导致总高度超出原始 bbox。

## 根因分析

### CJK vs 拉丁字体行高对比

| 指标 | 英文（拉丁字体） | 中文（CJK字体） |
|------|----------------|----------------|
| 字体大小 | 12pt | 12pt |
| 行高倍率 | ~1.2x | ~1.4x |
| 每行高度 | ~14.4pt | ~16.8pt |
| 行数 | 11 | 9 |
| **总高度** | **~158.4pt** | **~151.2pt** |

当 CJK 字体行高倍率为 1.5x 时（如 Arial Unicode）：

| 每行高度 | ~14.4pt | ~18pt |
| 行数 | 11 | 9 |
| **总高度** | **~158.4pt** | **~162pt** |

**162pt > 158.4pt → 溢出！** 中文文本虽然只有9行，但总高度仍超过原始 bbox。

### 代码层面的问题

1. `pdf_generator.py` 第283-290行：`insert_textbox()` 调用未使用 `lineheight` 参数，行高完全由字体内部度量决定
2. `pdf_generator.py` 第368-458行：`_get_suitable_font()` 从拉丁字体切换到 CJK 字体时，未对字体大小或行高做任何补偿
3. `pdf_generator.py` 第239行：bbox 高度来自原始英文布局，从未针对 CJK 字体调整

### PyMuPDF `insert_textbox` 的 `lineheight` 参数

PyMuPDF 的 `insert_textbox()` 支持 `lineheight` 参数，可以覆盖从字体属性计算的默认行高。当前代码未使用此参数。

## What Changes

- **在 `insert_textbox()` 调用中添加 `lineheight` 参数**：根据原文 bbox 高度和字体大小计算原文实际行高倍率，翻译文本使用相同行高倍率，确保翻译文本行高与原文一致

## Impact

- Affected code: `modules/pdf_generator.py` 的所有 `insert_textbox()` 调用
- 行为变更：所有翻译文本行高基于原文实际行高倍率，而非字体默认行高
- 影响范围：所有翻译 PDF 生成

## ADDED Requirements

### Requirement: 翻译文本使用与原文一致的行高

系统 SHALL 在渲染翻译文本时，根据原文 bbox 高度和字体大小计算原文实际行高倍率，并在 `insert_textbox()` 中使用相同行高倍率，确保翻译文本行高与原文一致。

#### Scenario: 计算原文行高倍率

- **WHEN** 渲染翻译文本
- **THEN** 根据 `bbox高度 / (字体大小 * 行数)` 计算原文行高倍率
- **AND** 将该倍率作为 `lineheight` 参数传入 `insert_textbox()`

#### Scenario: 翻译文本行高与原文一致

- **WHEN** 原文 11 行英文 bbox 高度为 158.4pt，字体大小 12pt
- **THEN** 原文行高倍率 = 158.4 / (12 * 11) ≈ 1.2
- **AND** 翻译文本使用 `lineheight=1.2`，9行中文总高度 = 12 * 1.2 * 9 = 129.6pt < 158.4pt

#### Scenario: 行高倍率下限保护

- **WHEN** 计算出的行高倍率小于 1.0
- **THEN** 使用默认值 1.2（防止异常值导致行高过小）

#### Scenario: 翻译文本不超出原始 bbox

- **WHEN** 翻译文本行数少于或等于原文行数
- **THEN** 翻译文本总高度不超过原始 bbox 高度

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
