# PDF/Word 表格对齐方式参照原表格配置 Spec

## Why

生成 PDF 和 Word 文档中的表格时，对齐方式全部硬编码（PDF 表格单元格固定居中 `align=1`，Word 表格固定 `WD_TABLE_ALIGNMENT.CENTER`），未参照原文 PDF 表格的实际对齐方式，导致表头居中但数据列左对齐等常见布局丢失，视觉还原度差。

**注**：PyMuPDF 的 `Table` 对象（v1.26.7）不提供原生对齐属性，`Span` 字典也只有 `origin`（基线起点）和 `bbox`，无 alignment 字段。因此对齐信息需从字符级 bbox 位置数据中提取。

## What Changes

- `PdfCell` 模型新增 `alignment` 属性（0=左对齐, 1=居中, 2=右对齐）
- 提取层在提取单元格文本时，利用已有的字符级 bbox 数据提取对齐信息（PyMuPDF 无原生对齐属性，需从字符位置计算）
- `PdfTable` 新增 `alignment` 属性表示表格整体对齐（基于 bbox 相对于页面位置提取）
- PDF 生成器使用 `PdfCell.alignment` 替代硬编码 `align=1`
- Word 生成器使用 `PdfCell.alignment` 设置单元格段落对齐，使用 `PdfTable.alignment` 设置表格整体对齐

## Impact

- Affected specs: 无
- Affected code:
  - `models/extraction.py` — PdfCell、PdfTable 新增 alignment 字段
  - `modules/extractors/coordinate_utils.py` — 新增对齐提取函数
  - `modules/extractors/table_processor.py` — 提取时从字符位置提取单元格对齐
  - `modules/ocr/paddle_extractor.py` — OCR 表格提取时从 textline 位置提取单元格对齐
  - `modules/pdf_generator.py` — 使用单元格对齐替代硬编码
  - `modules/docx_generator.py` — 使用单元格和表格对齐替代硬编码

## ADDED Requirements

### Requirement: PdfCell 新增 alignment 属性

PdfCell SHALL 新增 `alignment` 属性，取值 0（左对齐）、1（居中）、2（右对齐），默认值 0。

#### Scenario: 创建 PdfCell 时指定 alignment

- **WHEN** 创建 PdfCell 对象
- **THEN** 可通过参数指定 alignment，默认为 0（左对齐）
- **AND** `from_dict()` 和 `to_dict()` 正确序列化/反序列化 alignment

### Requirement: 提取层提取单元格对齐方式

提取层 SHALL 在提取单元格文本时，利用已有的字符级/textline 级 bbox 数据提取对齐信息。

#### Scenario: 非OCR表格（PyMuPDF 提取）

- **WHEN** 使用 `extract_table_cells_by_bbox` 提取表格
- **THEN** 对每个有文本的单元格，利用已分配到该单元格的字符 bbox 计算文本整体 bbox
- **AND** 比较文本整体 bbox 中心与单元格 bbox 中心的水平偏移
- **AND** 偏移 < 单元格宽度 15% → 居中 (1)
- **AND** 文本左边缘接近单元格左边缘（偏移 < 单元格宽度 10%）→ 左对齐 (0)
- **AND** 文本右边缘接近单元格右边缘（偏移 < 单元格宽度 10%）→ 右对齐 (2)
- **AND** 默认左对齐 (0)

#### Scenario: OCR表格（PaddleOCR 提取）

- **WHEN** 使用 PaddleOCR 提取表格
- **THEN** 使用 textline bbox 与单元格 bbox 的位置关系提取对齐
- **AND** 提取逻辑与非OCR表格一致

#### Scenario: 单元格无文本或 bbox 不可用

- **WHEN** 单元格文本为空或 bbox 不可用
- **THEN** alignment 默认为 0（左对齐）

### Requirement: PdfTable 新增 alignment 属性

PdfTable SHALL 新增 `alignment` 属性，表示表格整体在页面中的对齐方式。

#### Scenario: bbox 可用时提取表格对齐

- **WHEN** PdfTable.bbox 有效
- **THEN** 根据 bbox 中心与页面中心的水平偏移提取表格对齐
- **AND** 偏移 < 页面宽度 5% → 居中 (1)
- **AND** bbox 左边缘接近页面左边缘 → 左对齐 (0)
- **AND** bbox 右边缘接近页面右边缘 → 右对齐 (2)

#### Scenario: bbox 不可用

- **WHEN** PdfTable.bbox 为空
- **THEN** alignment 默认为 1（居中），与当前行为一致

### Requirement: PDF 生成器使用单元格对齐

PDF 生成器绘制表格单元格文本时 SHALL 使用 `PdfCell.alignment` 替代硬编码 `align=1`。

#### Scenario: 单元格有 alignment 属性

- **WHEN** 绘制表格单元格文本
- **THEN** 使用 `cell.alignment` 作为 `insert_textbox` 的 `align` 参数
- **AND** alignment 为 0/1/2 分别对应左对齐/居中/右对齐

#### Scenario: 单元格无 alignment 属性

- **WHEN** 单元格 alignment 未设置
- **THEN** 使用默认值 1（居中），与当前行为一致

### Requirement: Word 生成器使用单元格和表格对齐

Word 生成器 SHALL 使用 `PdfCell.alignment` 设置单元格段落对齐，使用 `PdfTable.alignment` 设置表格整体对齐。

#### Scenario: 设置单元格段落对齐

- **WHEN** 写入表格单元格文本
- **THEN** 根据 `cell.alignment` 设置段落对齐方式
- **AND** 0 → `WD_ALIGN_PARAGRAPH.LEFT`
- **AND** 1 → `WD_ALIGN_PARAGRAPH.CENTER`
- **AND** 2 → `WD_ALIGN_PARAGRAPH.RIGHT`

#### Scenario: 设置表格整体对齐

- **WHEN** 创建 Word 表格
- **THEN** 根据 `table.alignment` 设置 `word_table.alignment`
- **AND** 0 → `WD_TABLE_ALIGNMENT.LEFT`
- **AND** 1 → `WD_TABLE_ALIGNMENT.CENTER`
- **AND** 2 → `WD_TABLE_ALIGNMENT.RIGHT`

## MODIFIED Requirements

无

## REMOVED Requirements

无
