# 全面修复表格 OCR 识别与翻译流程 Spec

## Why

OCR 模式下整个章节关联流程被跳过（`pdf_extractor.py` 第259行直接 return），导致文本块、表格、图像均无章节关联，章节拆分输出丢失所有内容。此外表格还存在多个问题：PDF 输出中渲染位置错误（使用硬编码坐标）、同一页多表格共享第一个表格的 bbox、逐单元格翻译 API 调用开销大、单元格缺少 bbox 信息、Word 输出无样式、Markdown 输出首行总当表头。

## What Changes

- **修复 OCR 模式章节关联**：在 OCR 提取结果返回后补充完整的章节关联流程（书签提取 + 文本块/表格/图像关联）
- **修复多表格 bbox bug**：`_process_page_tables` 中按索引匹配每个表格的 bbox
- **修复 OCR 模式 PDF 表格渲染**：基于表格 bbox 和单元格行列数计算等分网格布局
- **优化表格翻译批量化**：将逐单元格翻译改为按行批量翻译
- **OCR 模式补充单元格 bbox**：基于表格 bbox 和行列数计算每个单元格的近似 bbox
- **Word 表格添加基本样式**：添加边框和字体设置
- **Markdown 表格智能表头检测**：检测首行是否为表头行

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`、`modules/pdf_extractor.py`、`modules/pdf_generator.py`、`modules/docx_generator.py`、`modules/markdown_generator.py`、`services/translation_service.py`
- Affected specs: `fix-formula-predict-gil-hang`（同属 OCR 流程优化）

## ADDED Requirements

### Requirement: OCR 模式章节关联

系统 SHALL 在 OCR 模式提取结果返回后，补充完整的章节关联流程，与非 OCR 模式保持一致。包括：提取书签信息、关联文本块、关联表格、关联图像。

#### Scenario: OCR 模式含章节的文档

- **WHEN** OCR 模式提取 PDF 内容且文档有书签/章节信息
- **THEN** 文本块被正确关联到对应章节（`chapter_id`、`chapter_title` 等字段被填充）
- **AND** 表格被正确关联到对应章节
- **AND** 图像被正确关联到对应章节
- **AND** 章节拆分的 Markdown 输出包含对应章节的所有内容

#### Scenario: OCR 模式无章节的文档

- **WHEN** OCR 模式提取 PDF 内容且文档无书签
- **THEN** 章节关联流程正常执行但不产生关联（与无章节的非 OCR 模式一致）

### Requirement: 修复多表格 bbox 匹配

系统 SHALL 修复 `_process_page_tables` 中的多表格 bbox bug。`parsing_res_list` 中的 `table` block 与 `table_res_list` 通过索引一一对应，应按索引匹配每个表格的 bbox 而非总是取第一个。

#### Scenario: 同一页有多个表格

- **WHEN** 同一页包含 2 个以上表格
- **THEN** 每个表格获得各自对应的 bbox
- **AND** 不再出现所有表格共享第一个表格 bbox 的情况

### Requirement: OCR 模式补充单元格 bbox

系统 SHALL 在 OCR 模式下基于表格 bbox 和单元格行列数计算每个单元格的近似 bbox。将表格 bbox 等分为均匀网格，每个单元格获得对应的矩形区域。

#### Scenario: OCR 模式表格单元格 bbox

- **WHEN** OCR 模式识别表格且表格 bbox 有效（非 `(0,0,0,0)`）
- **THEN** 每个单元格基于表格 bbox 等分计算得到近似 bbox
- **AND** `PdfCell.bbox` 不再全部为 `(0,0,0,0)`

#### Scenario: 表格 bbox 无效

- **WHEN** 表格 bbox 为 `(0,0,0,0)` 或无效
- **THEN** 单元格 bbox 保持 `(0,0,0,0)`（无法计算）

### Requirement: 修复 OCR 模式 PDF 表格渲染位置

系统 SHALL 修复 PDF 输出中 OCR 模式表格的渲染位置。当 `row_heights` 和 `col_widths` 为空时，基于表格 bbox 和单元格行列数计算等分网格布局，替代硬编码坐标。

#### Scenario: OCR 模式表格 PDF 渲染

- **WHEN** OCR 模式提取的表格在 PDF 中渲染
- **AND** `row_heights` 和 `col_widths` 为空但 `table.bbox` 有效
- **THEN** 基于表格 bbox 等分计算单元格位置
- **AND** 不再使用硬编码坐标 `x0=50+j*100, y0=200+i*30`

### Requirement: 表格翻译批量化

系统 SHALL 将表格翻译从逐单元格调用改为按行批量翻译。将每行所有单元格文本拼接后一次翻译，减少 API 调用次数。

#### Scenario: 翻译含 10×5 表格的文档

- **WHEN** 翻译一个 10 行 5 列的表格
- **THEN** API 调用次数从最多 50 次减少到最多 10 次（每行一次）
- **AND** 翻译结果正确拆分回各单元格

#### Scenario: 单元格包含分隔符

- **WHEN** 单元格文本包含行内分隔符（如 `\n` 或 `|`）
- **THEN** 使用不冲突的分隔符拼接，翻译后正确拆分

### Requirement: Word 表格添加基本样式

系统 SHALL 在 Word 输出中为表格添加基本样式：边框和字体设置。

#### Scenario: Word 输出含表格

- **WHEN** 生成 Word 文档且包含翻译后的表格
- **THEN** 表格有可见边框
- **AND** 单元格文本使用合适的字体和字号

### Requirement: Markdown 表格智能表头检测

系统 SHALL 智能检测表格首行是否为表头行。当首行单元格内容全部为数字或为空时，不将其作为表头，而是添加空表头行。

#### Scenario: 表格首行是表头

- **WHEN** 表格首行包含非数字文本
- **THEN** 首行作为 Markdown 表头行

#### Scenario: 表格首行不是表头

- **WHEN** 表格首行全部为数字或为空
- **THEN** 添加空表头行，所有数据行作为表体

## MODIFIED Requirements

### Requirement: _process_page_tables bbox 匹配逻辑

从"取第一个 table block 的 bbox"改为"按索引取第 N 个 table block 的 bbox"。

### Requirement: translate_tables 翻译粒度

从"逐单元格翻译"改为"按行批量翻译"。

### Requirement: _draw_translated_table 位置计算

从"无 row_heights/col_widths 时使用硬编码坐标"改为"基于 table.bbox 等分计算"。

## REMOVED Requirements

（无移除的需求）
