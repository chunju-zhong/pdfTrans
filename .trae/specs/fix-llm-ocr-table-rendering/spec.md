# 修复 LLM OCR 表格未正确绘制 Spec

## Why
LLM OCR 模式识别到表格后，PDF 输出中表格没有正确绘制。根因分析：

1. **`_parse_html_table` 创建的单元格 bbox 全为 `(0,0,0,0)`**（[llm_extractor.py:668](modules/ocr/llm_extractor.py#L668)），没有计算真实的单元格坐标
2. **PdfTable 缺少 `row_heights` 和 `col_widths`**（[llm_extractor.py:370-375](modules/ocr/llm_extractor.py#L370-L375)），LLM OCR 创建 PdfTable 时未传入这两个关键属性
3. **`_parse_ref_tags_response` 返回空表格列表**（[llm_extractor.py:467](modules/ocr/llm_extractor.py#L467)），DeepSeek-OCR 原生格式的响应完全不提取表格
4. **`_parse_markdown_response` 也返回空表格列表**（[llm_extractor.py:307](modules/ocr/llm_extractor.py#L307)），Markdown 格式同样丢失表格

对比 PaddleOCR 路径（[table_processor.py:157-170](modules/extractors/table_processor.py#L157-L170)）会调用 `calculate_row_heights` / `calculate_col_widths` 计算行列尺寸，并传入 PdfTable，而 LLM OCR 路径完全跳过了这一步。

## What Changes
- 在 `llm_extractor.py` 的 `_parse_json_response` 中，创建 PdfTable 后自动计算 `row_heights` 和 `col_widths`
- 在 `_parse_html_table` 中，基于 table bbox 和单元格的 rowspan/colspan 计算每个单元格的真实 bbox
- 在 `_parse_ref_tags_response` 和 `_parse_markdown_response` 中增加表格检测：从响应文本中提取 `<table>...</table>` HTML 并解析为 PdfTable

## Impact
- Affected code: [llm_extractor.py](modules/ocr/llm_extractor.py)
- Affected code: [pdf_generator.py](modules/pdf_generator.py)（`_draw_translated_table` 的 fallback 分支验证）
- Affected specs: fix-llm-ocr-response-parsing

## ADDED Requirements

### Requirement: LLM OCR 表格行列尺寸计算
JSON 格式响应解析出的表格 SHALL 自动计算 `row_heights` 和 `col_widths`。

#### Scenario: JSON 响应包含表格
- **WHEN** LLM 返回 JSON 格式且 `tables` 数组非空
- **THEN** 解析 HTML 表格后，基于 table bbox 均匀分配计算每个单元格 bbox，并计算 `row_heights` / `col_widths` 传入 PdfTable

### Requirement: LLM OCR 单元格 bbox 计算
HTML 表格解析后的每个单元格 SHALL 有基于 table bbox 的估算坐标。

#### Scenario: 表格有有效 bbox
- **WHEN** table bbox 非零且非 `(0,0,0,0)`
- **THEN** 根据 rowspan/colspan 将 table bbox 均匀分割为各单元格 bbox

#### Scenario: 表格 bbox 无效
- **WHEN** table bbox 为 `(0,0,0,0)` 或 None
- **THEN** 所有单元格 bbox 保持 `(0,0,0,0)`，由 PDF generator 使用均匀分布 fallback 渲染

### Requirement: DeepSeek-OCR/Markdown 响应中的表格检测
非 JSON 格式的响应 SHALL 尝试从中提取 HTML 表格。

#### Scenario: 响应包含 `<table>` 标签
- **WHEN** 响应文本中包含 `<table>` HTML 标签
- **THEN** 提取并解析为 PdfTable，与其他格式返回的表格统一处理

## MODIFIED Requirements

### Requirement: _parse_json_response 表格构建
现有的 `_parse_json_response` 方法 SHALL 在创建 PdfTable 时补充计算行列尺寸。

### Requirement: _parse_html_table 单元格坐标
现有的 `_parse_html_table` 方法 SHALL 接受 table bbox 参数，用于计算单元格级坐标。
