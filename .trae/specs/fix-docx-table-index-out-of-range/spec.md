# 修复 LLM OCR 生成 Word 文档时 list index out of range Spec

## Why
LLM OCR 模式翻译 367 页 PDF 时，生成 Word 文档阶段崩溃：`翻译失败: 生成Word文档时出错: list index out of range`。根因是 `_add_table` 方法在处理 LLM OCR 返回的表格时，存在两个关键缺陷：

1. **列数计算错误**：使用 `len(table_data[0])` 获取列数，但 LLM OCR 的 `_parse_html_table` 返回的是锯齿数组（每行 cell 数量不一致），导致列数被严重低估
2. **合并单元格越界**：LLM 返回的 `rowspan`/`colspan` 值未经边界校验，`word_table.cell(i + row_span - 1, j + col_span - 1)` 直接越界

对比 PaddleOCR 路径使用 `_expand_html_table` 生成规整矩形矩阵，LLM OCR 路径缺少此步骤。

## What Changes
- 在 `llm_extractor.py` 的 `_parse_html_table` 中，复用 PaddleOCR 的 `_expand_html_table` 逻辑生成矩形矩阵，并裁剪 `rowspan`/`colspan` 不超出表格边界
- 在 `docx_generator.py` 的 `_add_table` 中，添加防御性边界检查：正确计算 `num_cols`、裁剪 merge 范围、安全遍历单元格

## Impact
- Affected code: [docx_generator.py](modules/docx_generator.py)（`_add_table` 方法）
- Affected code: [llm_extractor.py](modules/ocr/llm_extractor.py)（`_parse_html_table` 方法）
- Affected specs: fix-llm-ocr-table-rendering

## ADDED Requirements

### Requirement: LLM OCR 表格单元格矩阵规整化
`_parse_html_table` SHALL 返回规整的矩形二维矩阵（每行长度等于逻辑列数），合并单元格覆盖位置填充 `None`，与 PaddleOCR 路径的 `_expand_html_table` 输出格式一致。

#### Scenario: HTML 表格包含 colspan 单元格
- **WHEN** LLM 返回的 HTML 表格第一行有 `<td colspan="3">A</td>`，第二行有 3 个独立 `<td>`
- **THEN** `_parse_html_table` 返回的 cells 矩阵每行长度均为 3，第一行第 1 列为 PdfCell（col_span=3），第 2、3 列为 None

#### Scenario: HTML 表格包含 rowspan 单元格
- **WHEN** LLM 返回的 HTML 表格某单元格有 `rowspan="2"`
- **THEN** 被合并覆盖的下一行对应位置为 None，矩阵仍为矩形

### Requirement: rowspan/colspan 边界裁剪
`_parse_html_table` SHALL 将 `rowspan` 和 `colspan` 裁剪到不超出表格实际行列范围。

#### Scenario: LLM 返回的 rowspan 超出表格行数
- **WHEN** 表格有 3 行，某单元格 `rowspan="5"`
- **THEN** rowspan 被裁剪为 `3 - row_idx`，确保不越界

#### Scenario: LLM 返回的 colspan 超出表格列数
- **WHEN** 表格有 4 列，某单元格 `colspan="6"` 且起始列 idx=2
- **THEN** colspan 被裁剪为 `4 - 2`，确保不越界

### Requirement: _add_table 防御性列数计算
`_add_table` SHALL 使用所有行中的最大逻辑列数（考虑 `col_span`）计算 `num_cols`，而非仅取第一行长度。

#### Scenario: 表格第一行有合并单元格
- **WHEN** `table_data[0]` 有 1 个 `col_span=3` 的单元格，`table_data[1]` 有 3 个独立单元格
- **THEN** `num_cols` 计算为 3（而非 1）

### Requirement: _add_table 合并操作边界保护
`_add_table` 在执行 `word_table.cell().merge()` 前 SHALL 裁剪 merge 范围到表格实际行列范围内。

#### Scenario: 单元格 row_span 超出 Word 表格行数
- **WHEN** Word 表格有 4 行，单元格 (i=2, row_span=3) 导致 merge 目标行为 4（超出 0-3 范围）
- **THEN** merge 目标行被裁剪为 `min(i + row_span - 1, num_rows - 1)` = 3

## MODIFIED Requirements

### Requirement: _parse_html_table 返回格式
现有的 `_parse_html_table` 方法 SHALL 返回规整矩形矩阵而非锯齿数组。调用方（`_parse_json_response`、`_parse_ref_tags_response`）无需修改，因为它们只将 cells 传入 PdfTable 构造函数。

### Requirement: _add_table 单元格遍历
现有的 `_add_table` 方法 SHALL 安全处理 `None` 单元格和超出 Word 表格列数的单元格索引。
