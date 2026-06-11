# 修复步骤1版面分析无法检测公式区域 Spec

## Why
步骤1创建 PP-StructureV3 管线时 `use_formula=False`，导致版面分析模型不会输出 `formula`/`formula_number` 标签。步骤3根据 `has_formula` 判断是否执行公式识别，但由于步骤1从未检测到公式区域，`formula_pages` 始终为空，步骤3永远不会触发。这是一个鸡生蛋的设计缺陷。

## What Changes
- 步骤1创建管线时 `use_formula=True`，使版面分析模型能检测公式区域
- 步骤1管线启用公式识别后，内存会增加，需要评估影响

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`
- Affected specs: optimize-ocr-memory（步骤1内存可能增加）

## ADDED Requirements

### Requirement: 步骤1版面分析启用公式检测
系统 SHALL 在步骤1创建 PP-StructureV3 管线时启用公式识别（`use_formula=True`），使版面分析模型能输出 `formula`/`formula_number` 标签。

#### Scenario: 页面包含公式时步骤3被触发
- **WHEN** PDF 页面包含数学公式，步骤1版面分析检测到 `formula` 标签
- **THEN** `has_formula=True`，步骤3公式识别被执行

#### Scenario: 页面不包含公式时步骤3不执行
- **WHEN** PDF 页面不包含数学公式，步骤1版面分析未检测到 `formula` 标签
- **THEN** `has_formula=False`，步骤3跳过

## MODIFIED Requirements

### Requirement: 步骤1管线创建参数
`_create_pipeline(use_table=False, use_formula=True, use_region_detection=False)` — 将 `use_formula` 从 `False` 改为 `True`。
