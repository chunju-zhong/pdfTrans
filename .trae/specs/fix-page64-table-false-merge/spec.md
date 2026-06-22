# 修复 PyMuPDF 不完整表格检测导致数据行丢失和误合并 Spec

## Why
第64页表格在输出PDF中出现"单元格被合并"的视觉问题。根因是 PyMuPDF 的 `page.find_tables()` 仅检测到表头行（1行×6列），数据行（C4, The Pile, RedPajama 等）未被识别为表格的一部分，被提取为普通文本块。这些文本块经语义合并后形成跨多列的大块文本，渲染后视觉上呈现为"合并单元格"。

具体问题链：
1. PyMuPDF `find_tables()` 默认使用 lines 策略，依赖可见网格线检测表格。第64页表格的数据行没有水平分隔线，因此只检测到有网格线的表头行
2. 数据行被 `page.get_text("blocks")` 提取为普通文本块，每个文本块跨越2-3列
3. 部分文本块（如包含 "Public?/C4/Common Crawl/..." 的 Block 4）与表头单元格重叠超过50%，被 `is_table_text` 过滤掉，导致数据丢失
4. 未被过滤的数据行文本块经 `merge_semantic_blocks` 合并后，形成跨整个表格宽度的大块文本
5. 渲染时这些大块文本覆盖多列区域，视觉上表现为"合并单元格"

诊断证据：
- 默认策略（lines）：1个表格，1行×6列，bbox=(72.04, 188.95, 431.96, 213.55)
- text策略：1个表格，52行×7列，包含整页内容（过于激进）
- text策略+clip裁剪：1个表格，30行×7列，包含表头和数据行但列数不对（7列而非6列）
- 数据行文本块示例：Block 6 "The Pile\nCommon Crawl, PubMed..." bbox=(75.6, 238.1, 216.3, 278.5) 跨越前2列

## What Changes
- 在 `table_processor.py` 的 `extract_tables_by_pymupdf` 中增加不完整表格检测和扩展逻辑
- 使用表头行的列边界 + 文本块行边界，通过字符级重叠分配提取数据行单元格
- 将被扩展进表格的文本块从页面的 text_blocks 中移除，避免重复渲染

## Impact
- Affected code: `modules/extractors/table_processor.py` 中的 `extract_tables_by_pymupdf` 函数
- Affected code: `modules/pdf_extractor.py` 中的文本块提取逻辑（扩展后的表格 bbox 自动过滤数据行文本块）
- Affected code: `modules/extractors/coordinate_utils.py` 中新增工具函数
- 影响范围：所有使用 PyMuPDF 提取路径的表格（非LLM OCR模式）

## 算法设计

### Step 1: 不完整表格检测

对 `find_tables()` 检测到的每个表格：

1. 获取表格行数 `row_count`
2. 如果 `row_count >= 3`，跳过（认为表格完整）
3. 如果 `row_count <= 2`：
   a. 获取表格的 x 范围 `[table_x0, table_x1]` 和底部 y 坐标 `table_bottom`
   b. 获取页面上所有文本块
   c. 查找满足以下条件的文本块：
      - `block_y0 > table_bottom - tolerance`（在表格下方或与表格底部齐平）
      - `block_x0 < table_x1` 且 `block_x1 > table_x0`（与表格 x 范围有重叠）
      - 重叠比例 > 50%（`overlap_width / block_width > 0.5`）
   d. 如果存在这样的文本块，标记表格为"可能不完整"

### Step 2: 确定数据行区域边界

1. 从表头底部 `table_bottom` 开始，向下扫描文本块
2. 收集所有与表格 x 范围重叠 > 50% 的文本块，按 y0 排序
3. 确定表格底部边界：
   - 遍历排序后的文本块，当两个相邻文本块的 y 间距 > `gap_threshold`（默认 25pt，约为1.5倍行高）时，认为表格结束
   - 或者当文本块的宽度 > `table_x1 - table_x0 + 50pt`（跨出表格范围太多，可能是段落文字）时，认为表格结束
4. 扩展区域为 `[table_x0, table_y0, table_x1, extended_bottom]`

### Step 3: 确定数据行行边界

1. 将步骤2收集的文本块按 y0 分组：y0 差值 < `row_group_tolerance`（默认 5pt）的文本块属于同一行
2. 对每组，行边界为 `(min(block_y0), max(block_y1))`
3. 结果：`data_row_boundaries = [(row_y0, row_y1), ...]`，按 y0 升序排列

### Step 4: 使用列边界 + 行边界构建数据行单元格

1. 从表头行获取列边界：`col_boundaries = [(col_x0, col_x1), ...]`（共 num_cols 列）
2. 对每个数据行 `r`，对每列 `c`，构建单元格 bbox：
   `cell_bbox = (col_boundaries[c][0], row_boundaries[r][0], col_boundaries[c][1], row_boundaries[r][1])`
3. 获取扩展区域内所有字符（复用 `extract_table_cells_by_bbox` 中的字符提取逻辑）
4. 对每个字符，按50%面积重叠分配到最佳单元格（复用现有逻辑）
5. 将每个单元格的字符按 (y0, x0) 排序并拼接为文本
6. 结果：`data_rows = [[cell_text, ...], ...]`，每行 num_cols 列

### Step 5: 构建完整表格

1. 合并表头行和数据行：`all_data = [header_row] + data_rows`
2. 构建 `rows_data`（bbox 矩阵）：
   - 表头行：使用原始 `rows_data`
   - 数据行：使用 Step 4 构建的单元格 bbox
3. 构建 `bbox_matrix = _build_bbox_matrix(rows_data, num_rows, num_cols)`
4. 调用 `compute_span_from_none_positions(bbox_matrix, ...)` 推断合并单元格
5. 创建 PdfCell 对象，构建 cell_matrix
6. 计算行高和列宽（包含新增数据行）
7. 创建 PdfTable 对象，替换原始不完整表格

### Step 6: 更新返回值

1. 更新 `page_table_cells[page_num]`：包含扩展后表格的所有单元格 bbox
2. 更新 `page_tables[page_num]`：包含扩展后的表格 bbox
3. `pdf_extractor.py` 的 `_extract_text_blocks` 无需修改——扩展后的单元格 bbox 会自动使数据行文本块的 `is_table_text = True`，从而被正确过滤

## ADDED Requirements

### Requirement: 不完整表格检测
系统 SHALL 在 PyMuPDF 默认策略检测到表格后，判断表格是否可能不完整。

#### Scenario: 表格仅含表头行
- **WHEN** 默认策略检测到的表格仅有1-2行
- **AND** 表格下方存在与表格x范围重叠>50%的文本块
- **THEN** 标记该表格为"可能不完整"，触发扩展检测

#### Scenario: 表格行数充足
- **WHEN** 默认策略检测到的表格有3行及以上
- **THEN** 不触发扩展检测，保持当前行为

#### Scenario: 表格下方无对齐文本块
- **WHEN** 默认策略检测到的表格仅有1-2行
- **AND** 表格下方不存在与表格x范围重叠>50%的文本块
- **THEN** 不触发扩展检测，保持当前行为（表格可能确实只有表头）

### Requirement: 数据行区域边界确定
系统 SHALL 通过扫描表格下方的文本块确定数据行的覆盖区域。

#### Scenario: 连续文本块延伸表格
- **WHEN** 表格下方存在连续的、与表格x范围重叠>50%的文本块
- **AND** 相邻文本块的y间距 ≤ 25pt
- **THEN** 这些文本块覆盖的区域为数据行区域

#### Scenario: 大间距中断表格
- **WHEN** 两个相邻文本块的y间距 > 25pt
- **THEN** 表格在间距前的最后一个文本块底部结束

#### Scenario: 宽文本块中断表格
- **WHEN** 某文本块的宽度 > 表格宽度 + 50pt
- **THEN** 该文本块不属于表格，表格在前一个文本块底部结束

### Requirement: 数据行行边界确定
系统 SHALL 将数据行区域内的文本块按y坐标分组，确定每行的上下边界。

#### Scenario: 同行文本块分组
- **WHEN** 多个文本块的 y0 差值 < 5pt
- **THEN** 这些文本块属于同一行，行边界为 (min_y0, max_y1)

#### Scenario: 不同行文本块
- **WHEN** 两个文本块的 y0 差值 ≥ 5pt
- **THEN** 它们属于不同的行

### Requirement: 使用列边界提取数据行单元格
系统 SHALL 使用表头行的列边界和文本块的行边界，通过字符级重叠分配提取数据行单元格内容。

#### Scenario: 字符分配到单元格
- **WHEN** 某字符与某单元格的面积重叠 > 50%
- **THEN** 该字符被分配到该单元格

#### Scenario: 字符不与任何单元格重叠
- **WHEN** 某字符与所有单元格的面积重叠均 ≤ 50%
- **THEN** 该字符被忽略（可能是噪声或边界字符）

#### Scenario: 空单元格
- **WHEN** 某单元格没有被分配任何字符
- **THEN** 该单元格文本为空字符串 ""（不是 None，因为没有合并单元格）

### Requirement: 完整表格构建
系统 SHALL 将表头行和数据行合并为完整的 PdfTable 对象。

#### Scenario: 成功扩展
- **WHEN** 数据行被成功提取
- **THEN** 构建包含表头+数据行的完整表格，bbox 覆盖整个表格区域
- **AND** 行高和列宽包含所有数据行
- **AND** page_table_cells 包含所有单元格 bbox

#### Scenario: 扩展失败
- **WHEN** 数据行提取过程中出现异常
- **THEN** 回退到原始不完整表格，记录 WARNING 日志

## MODIFIED Requirements

### Requirement: extract_tables_by_pymupdf 返回值
返回值类型不变（3元组），但 `page_table_cells` 需要包含扩展后表格的所有单元格 bbox，供 `pdf_extractor.py` 的文本块过滤逻辑使用。

### Requirement: pdf_extractor.py 文本块过滤
`_extract_text_blocks` 中的 `is_table_text` 判断逻辑不变，但由于表格 bbox 和单元格 bbox 已扩展，更多数据行文本块会被正确过滤（不再被语义合并处理）。

## REMOVED Requirements

### Requirement: _build_bbox_matrix 使用哨兵值区分填充和合并
**Reason**: 原spec基于错误的根因分析。第64页表格的真正问题不是 `_build_bbox_matrix` 的 None 填充导致误合并，而是 PyMuPDF 不完整表格检测导致数据行被当作普通文本处理。哨兵值方案对解决此问题无帮助。
**Migration**: 如果未来确实出现因 None 填充导致的误合并问题，可以重新引入哨兵值方案。
