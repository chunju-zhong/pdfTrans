# 步骤1启用公式识别以修复行内公式漏检 Spec

## Why
步骤1创建 PP-StructureV3 管线时 `use_formula=False`，版面分析模型不会输出 `formula`/`formula_number` 标签。日志证实第34页的行内公式（如 `C:14,58-（039*T)+(0007*T2)-(000`、`2*10⁻³ = Oxygen requirement(kg`）被误标为 `text`，导致步骤3公式识别从未触发，公式只得到不准确的 OCR 文本而非 LaTeX。

## What Changes
- 步骤1创建管线时 `use_formula=True`，使版面分析模型能检测公式区域并直接输出 LaTeX 结果
- 步骤1的 `_process_page_layout` 从 `formula_res_list` 提取公式 TextBlock
- **移除步骤3**（公式识别），因为步骤1已包含公式识别功能，步骤3是冗余的重复工作
- 步骤1内存占用会增加（公式模型约 200MB），需调整内存上限

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`
- Affected specs: optimize-ocr-memory（步骤1内存增加约 200MB）

## ADDED Requirements

### Requirement: 步骤1版面分析启用公式检测
系统 SHALL 在步骤1创建 PP-StructureV3 管线时启用公式识别（`use_formula=True`），使版面分析模型能输出 `formula`/`formula_number` 标签及 `formula_res_list`。

#### Scenario: 行内公式被正确检测
- **WHEN** PDF 页面包含行内公式（如 `C:14,58-（039*T)+(0007*T2)`）
- **THEN** 步骤1版面分析将公式区域标记为 `formula` 标签，`has_formula=True`

#### Scenario: 步骤1直接提取 LaTeX
- **WHEN** 步骤1管线启用 `use_formula=True` 且页面包含公式
- **THEN** `formula_res_list` 包含 LaTeX 识别结果，步骤1直接生成 `is_formula=True` 的 TextBlock

#### Scenario: 内存不足时优雅降级
- **WHEN** 步骤1创建管线时可用内存不足以同时加载版面分析+公式识别模型
- **THEN** 系统回退到 `use_formula=False` 模式，并记录警告日志

## MODIFIED Requirements

### Requirement: 步骤1管线创建参数
`_create_pipeline(use_table=False, use_formula=True, use_region_detection=False)` — 将 `use_formula` 从 `False` 改为 `True`。

### Requirement: 步骤1内存上限
步骤1启用公式识别后，`MEMORY_CAP_LAYOUT` 上限 SHALL 从 1600MB 调整为 1800MB，以容纳额外的公式识别模型（约 200MB）。

## REMOVED Requirements

### Requirement: 步骤3公式识别
**Reason**: 步骤1启用 `use_formula=True` 后，`pipeline.predict()` 直接返回 `formula_res_list`，步骤3用另一个管线对同一页面重新识别是冗余的重复工作，浪费内存和时间。
**Migration**: 步骤1的 `_process_page_layout` 直接从 `formula_res_list` 提取公式 TextBlock，不再需要步骤3的独立管线。
