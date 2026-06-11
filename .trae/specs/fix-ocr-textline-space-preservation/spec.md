# 修复38页OCR文本空格丢失问题 Spec

## Why

PP-StructureV3 的 `block.content` 在版面分析阶段合并多行文本时，经常丢失单词间的空格，导致输出如 `abSalzgehalten>2gTDS/I`、`keineweiteren`、`imWesentlichenEinflussvon` 等连字文本。而 `overall_ocr_res` 中的 textline 级别 OCR 结果保留了正确的空格，但当前代码仅使用 `rec_boxes` 做字体大小估算，未使用 textline 级别的文本内容。

## What Changes

- **使用 `overall_ocr_res` 的 textline 级别文本替代 `block.content`**：从 `overall_ocr_res` 中提取 `rec_text`，按 block bbox 范围匹配 textline，拼接 textline 文本作为 block 的最终文本内容
- **保留 `block.content` 作为 fallback**：当 `overall_ocr_res` 不可用或匹配不到 textline 时，仍使用 `block.content`

## Impact

- Affected code: `modules/ocr/paddle_extractor.py` 的 `_process_page_layout` 方法
- 行为变更：文本块的文本内容来源从 `block.content` 改为 `overall_ocr_res` 的 textline 文本拼接

## ADDED Requirements

### Requirement: 使用 textline 级别文本替代 block.content

系统 SHALL 优先使用 `overall_ocr_res` 中的 textline 级别文本（`rec_text`）来构建文本块内容，而非直接使用 `block.content`。

#### Scenario: overall_ocr_res 可用且包含 rec_text

- **WHEN** `overall_ocr_res` 不为 None 且包含 `rec_text` 字段
- **THEN** 对于每个 block，找到落在其 bbox 范围内的 textline，按 y 坐标排序后拼接 `rec_text`，用拼接结果替代 `block.content`

#### Scenario: overall_ocr_res 不可用或无 rec_text

- **WHEN** `overall_ocr_res` 为 None 或不包含 `rec_text`
- **THEN** 使用 `block.content` 作为文本内容（当前行为）

#### Scenario: textline 匹配结果为空

- **WHEN** 某个 block 的 bbox 范围内没有匹配到任何 textline
- **THEN** 使用 `block.content` 作为文本内容（fallback）

## MODIFIED Requirements

### Requirement: _process_page_layout 文本提取逻辑

`_process_page_layout` 中的文本提取逻辑 SHALL 在提取 `rec_boxes` 的同时提取 `rec_text`，并在构建 TextBlock 时优先使用 textline 文本拼接结果。

## REMOVED Requirements

（无移除的需求）

## 根因分析

### 问题：38页文本空格丢失

从日志中对比不同运行的结果：

**第一次运行（18:46，2页）**：
- `text='Auslegungder Beluftung Ermittl'` — "der"和"Beluftung"之间缺少空格
- `text='abSalzgehalten>2gTDS/I \nkeinew'` — 多处空格丢失

**后续运行（20:54，1页）**：
- `text='AuslegungderBeluftung Ermittlu'` — 更严重，"AuslegungderBeluftung"完全连在一起
- `text='abSalzgehalten>2 g TDS/I \nkein'` — 这次 "2 g TDS/I" 有空格

**根因**：PP-StructureV3 的 `block.content` 是版面分析阶段将多行 OCR 结果合并后的文本。在合并过程中，行内单词间的空格经常丢失。而 `overall_ocr_res` 中的 textline 级别 OCR 结果（`rec_text`）是逐行识别的，保留了正确的空格。

**修改方案**：在 `_process_page_layout` 中，从 `overall_ocr_res` 同时提取 `rec_text` 和 `rec_boxes`。对于每个 block，找到落在其 bbox 范围内的 textline，按 y 坐标排序后拼接 `rec_text`，用拼接结果替代 `block.content`。
