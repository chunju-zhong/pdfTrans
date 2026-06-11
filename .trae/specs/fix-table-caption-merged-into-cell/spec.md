# 修复非OCR模式下表格标题/脚注被错误合并进表格最后一行单元格 Spec

## Why

非OCR模式（PyMuPDF）下，第22页的表格标题 "Table 5. An example of role prompting" 和表格后的段落 "The above example shows..." 被错误地合并进表格最后一行的单元格中，导致：
1. 这些文本作为表格单元格内容被翻译和渲染，位置错误（显示在表格最后一行内）
2. 这些文本无法作为独立文本块被正确翻译和放置在表格下方

## 根因分析（深度研究后更新）

### 之前的修复方案无效

之前实现的 `extract_table_cells_by_bbox` 函数（使用 `table.rows` 的单元格 bbox + 50%面积重叠判断替代 `table.extract()`）**没有解决问题**。日志确认该函数被调用了，但最后一行单元格仍然包含标题文本。

### 真正的根因：PyMuPDF `table.rows` 返回的最后一行单元格 bbox 本身就过大

PyMuPDF 的 `page.find_tables()` 在检测表格时，会将表格下方的标题/脚注文本也纳入最后一行单元格的 bbox 范围。这不是 `table.extract()` 的文本归属算法问题，而是**表格检测阶段就已经将标题/脚注区域划入了最后一行单元格**。

从翻译后 PDF 的调试结果可以验证：翻译后的 PDF 中，"back prompt (Table 9):" 文本与最后一行 cell0 有 83.2% 的重叠，说明这些文本确实落在了 PyMuPDF 检测到的单元格 bbox 内。原始 PDF 中 "Table 5. An example of role prompting" 的情况类似。

### 根本解决方案：后处理检测并分离表格标题/脚注

由于无法从 PyMuPDF 的表格检测结果中区分"真正的单元格文本"和"被错误纳入的标题/脚注文本"，必须在提取后做后处理：
1. 检测单元格文本中是否包含表格标题模式（如 "Table/Figure X."）
2. 将匹配的标题文本及其后续段落文本从单元格中分离
3. 分离出的文本作为独立文本块参与翻译

### OCR模式表格生成逻辑的影响

对比 develop 分支，OCR模式的 `refactor-table-to-grid-layout` 变更只修改了 `paddle_extractor.py`，不影响非OCR模式的 `table_processor.py`。非OCR模式的表格生成逻辑没有变化，问题一直存在。

## What Changes

- **回退 `extract_table_cells_by_bbox` 方案**：该方案无效，恢复使用 `table.extract()`
- **新增后处理**：在 `table_processor.py` 中对 `table.extract()` 返回的单元格文本做后处理，检测并分离表格标题/脚注
- **分离出的文本作为独立文本块**：创建 TextBlock 对象加入翻译流程
- **保留 `page_table_cells` 返回值**：文本块排除逻辑使用单元格 bbox 仍然有效

## Impact

- Affected code: `modules/extractors/table_processor.py`, `modules/pdf_extractor.py`

## ADDED Requirements

### Requirement: 表格单元格文本后处理——分离表格标题和脚注

系统在非OCR模式下提取表格后，SHALL 对 `table.extract()` 返回的单元格文本进行后处理，检测并分离表格标题和脚注文本。

#### Scenario: 最后一行单元格包含表格标题

- **WHEN** `table.extract()` 返回的最后一行单元格文本中包含匹配 "Table/Figure X." 模式的文本
- **THEN** 系统将该匹配的标题文本从单元格中分离出来
- **AND** 分离出的标题文本作为独立的 TextBlock 返回
- **AND** 单元格中仅保留实际的表格数据文本

#### Scenario: 最后一行单元格包含表格标题后的段落文本

- **WHEN** 表格标题文本之后还有额外的段落文本（如 "The above example shows..."）
- **THEN** 系统将这些段落文本也从单元格中分离出来
- **AND** 分离出的段落文本作为独立的 TextBlock 返回

#### Scenario: 单元格文本全部为标题/脚注

- **WHEN** 分离标题和脚注后，某行单元格的所有文本都被分离
- **THEN** 该行从表格中移除，表格行数相应减少

#### Scenario: 单元格文本不包含标题/脚注

- **WHEN** `table.extract()` 返回的单元格文本不包含 "Table/Figure X." 模式
- **THEN** 保持原始行为，不做任何修改

### Requirement: 分离的表格标题/脚注文本作为独立 TextBlock 参与翻译

系统 SHALL 将从表格单元格中分离出的标题/脚注文本作为独立的 TextBlock 返回。

#### Scenario: 表格标题 TextBlock

- **WHEN** 从表格单元格中分离出 "Table X. ..." 格式的标题文本
- **THEN** 创建一个 TextBlock 对象，bbox 位于表格 bbox 下方紧邻位置
- **AND** 该 TextBlock 被加入文本块列表参与翻译

#### Scenario: 表格脚注 TextBlock

- **WHEN** 从表格单元格中分离出表格后的段落文本
- **THEN** 创建一个 TextBlock 对象，bbox 位于表格标题 TextBlock 下方
- **AND** 该 TextBlock 被加入文本块列表参与翻译

## MODIFIED Requirements

### Requirement: extract_table_cells_by_bbox 替换为后处理方案

将之前实现的 `extract_table_cells_by_bbox` 函数替换为后处理方案：

修改前（当前无效实现）：
```python
data = extract_table_cells_by_bbox(page, table)
```

修改后：
```python
data = table.extract()
data, separated_texts = separate_table_caption_and_footnote(data, table.bbox)
```

新函数 `separate_table_caption_and_footnote` 的逻辑：
1. 遍历最后一行（和第一行）的每个单元格文本
2. 使用正则匹配 "Table/Figure\s+\d+[\.\:]" 模式，定位标题文本的起始位置
3. 将标题文本及其后的所有文本从单元格中分离
4. 如果分离后某行所有单元格为空，移除该行
5. 返回 `(cleaned_data, separated_texts)`，其中 `separated_texts` 是分离出的文本列表

### Requirement: extract_tables_by_pymupdf 返回值

返回值保持三元组 `(pdf_tables, page_tables, page_table_cells)`，但 `page_table_cells` 的数据来源恢复为 `table.cells`（不再依赖 `extract_table_cells_by_bbox`）。

新增第四个返回值 `separated_text_blocks`：

```python
return pdf_tables, page_tables, page_table_cells, separated_text_blocks
```

其中 `separated_text_blocks` 是一个列表，每个元素是包含 `page_num`, `text`, `bbox` 等信息的字典。

### Requirement: pdf_extractor.py 集成分离的文本块

`pdf_extractor.py` 中：
1. 接收 `separated_text_blocks` 参数
2. 将分离出的文本块转换为 TextBlock 对象，加入 text_blocks 列表
3. 文本块排除逻辑继续使用 `page_table_cells`（单元格 bbox 联合区域）

## REMOVED Requirements

### Requirement: 使用单元格精确 bbox 提取表格文本，替代 `table.extract()`

**Reason**：该方案无效。PyMuPDF `table.rows` 返回的最后一行单元格 bbox 本身就覆盖了标题区域，50%面积重叠判断无法排除标题字符。
**Migration**：恢复使用 `table.extract()`，改为后处理方案分离标题/脚注。
