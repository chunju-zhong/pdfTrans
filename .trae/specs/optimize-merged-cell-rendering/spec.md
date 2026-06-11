# 优化合并单元格渲染 Spec

## Why

合并单元格在输出 PDF 中存在两个问题：
1. **文字显示不全**：合并单元格的文本被塞入单格大小的 bbox，字体过小导致文字截断
2. **线条分隔**：网格线按均匀网格绘制，穿过合并单元格内部，破坏了合并效果

根因：`PdfCell` 缺少 `row_span`/`col_span` 字段，`_TableHtmlParser` 丢弃了 `rowspan`/`colspan` 属性，`_compute_table_grid` 按均匀网格处理，`_draw_translated_table` 无条件绘制所有行列线。

## What Changes

- `PdfCell` 新增 `row_span` 和 `col_span` 字段（默认值 1）
- `_TableHtmlParser` 解析 `rowspan`/`colspan` 属性，展开为完整二维矩阵（起始位置放文本+span，被合并位置标记为占位 `None`）
- `_compute_table_grid` 为合并单元格分配跨行跨列的 bbox
- `_draw_translated_table` 跳过被合并位置的文本/背景绘制，网格线绘制时跳过合并单元格内部线条
- PyMuPDF 提取路径：利用 `rows_data` 中的合并信息设置 `row_span`/`col_span`

## Impact

- Affected specs: `refactor-table-to-grid-layout`、`fix-table-coverage-and-lines`
- Affected code:
  - `models/extraction.py`（PdfCell 新增字段）
  - `modules/ocr/paddle_extractor.py`（`_TableHtmlParser`、`_compute_table_grid`）
  - `modules/pdf_generator.py`（`_draw_translated_table`）
  - `modules/extractors/table_processor.py`（PyMuPDF 路径设置 span）

## ADDED Requirements

### Requirement: PdfCell 支持 row_span 和 col_span

`PdfCell` SHALL 新增 `row_span`（默认 1）和 `col_span`（默认 1）字段，表示单元格跨越的行数和列数。

#### Scenario: 普通单元格

- **WHEN** 创建 `PdfCell` 时未指定 `row_span`/`col_span`
- **THEN** `row_span=1`，`col_span=1`

#### Scenario: 合并单元格

- **WHEN** 创建 `PdfCell` 时指定 `row_span=2, col_span=3`
- **THEN** 该单元格跨越 2 行 3 列，其 bbox 应覆盖对应的网格区域

### Requirement: _TableHtmlParser 解析 rowspan/colspan

`_TableHtmlParser` SHALL 从 `<td>`/`<th>` 标签的属性中提取 `rowspan` 和 `colspan`，并将 HTML 表格展开为完整的二维矩阵。

#### Scenario: HTML 包含合并单元格

- **WHEN** 解析 `<td rowspan="2" colspan="3">text</td>`
- **THEN** 起始位置 (row_idx, col_idx) 的 `PdfCell` 设置 `row_span=2, col_span=3`，文本为 "text"
- **AND** 被合并的位置 (row_idx, col_idx+1), (row_idx, col_idx+2), (row_idx+1, col_idx), (row_idx+1, col_idx+1), (row_idx+1, col_idx+2) 设为 `None`

#### Scenario: HTML 无合并属性

- **WHEN** 解析 `<td>text</td>`
- **THEN** 行为与当前一致，`row_span=1, col_span=1`

### Requirement: _compute_table_grid 为合并单元格分配跨行跨列 bbox

`_compute_table_grid` SHALL 识别合并单元格，为其分配覆盖多行多列的 bbox。

#### Scenario: 合并单元格跨 2 行 3 列

- **WHEN** 单元格 (0,0) 的 `row_span=2, col_span=3`
- **THEN** 该单元格的 bbox 从第 0 行顶部延伸到第 1 行底部，从第 0 列左侧延伸到第 2 列右侧
- **AND** 被合并位置的单元格 bbox 仍按单格计算（它们不会被绘制）

### Requirement: _draw_translated_table 跳过被合并位置

渲染表格时 SHALL 跳过被合并位置的背景和文本绘制。

#### Scenario: 单元格是被合并位置

- **WHEN** 遍历到 `cell is None` 或 `cell.row_span == 0`（占位标记）
- **THEN** 跳过该位置的背景绘制和文本绘制

### Requirement: 网格线绘制跳过合并单元格内部

网格线绘制 SHALL 根据合并信息跳过合并单元格内部的线条。

#### Scenario: 合并单元格跨 2 行 3 列

- **WHEN** 单元格 (0,0) 的 `row_span=2, col_span=3`
- **THEN** 不绘制第 0 行底部在列 0-2 范围内的水平线
- **AND** 不绘制列 0 右侧和列 1 右侧在第 0-1 行范围内的垂直线

#### Scenario: 普通单元格

- **WHEN** 单元格的 `row_span=1, col_span=1`
- **THEN** 正常绘制所有行列线

### Requirement: PyMuPDF 路径设置 row_span/col_span

PyMuPDF 提取路径 SHALL 利用 `rows_data` 中的合并信息为 `PdfCell` 设置 `row_span`/`col_span`。

#### Scenario: PyMuPDF 检测到合并单元格

- **WHEN** `rows_data` 中某单元格的 bbox 跨越多行或多列
- **THEN** 计算该单元格的 `row_span` 和 `col_span`，设置到 `PdfCell` 上
- **AND** 被合并位置设为 `None`

## MODIFIED Requirements

### Requirement: _TableHtmlParser 返回包含 span 信息的单元格

将 `_TableHtmlParser` 的输出从纯文本二维列表改为包含 `row_span`/`col_span` 的 `PdfCell` 对象二维列表。

```python
class _TableHtmlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []          # 每行: list of (text, rowspan, colspan)
        self.current_row = []
        self.current_cell = ''
        self.current_rowspan = 1
        self.current_colspan = 1
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag in ('td', 'th'):
            self.in_cell = True
            self.current_cell = ''
            self.current_rowspan = 1
            self.current_colspan = 1
            for attr_name, attr_value in attrs:
                if attr_name == 'rowspan':
                    self.current_rowspan = int(attr_value)
                elif attr_name == 'colspan':
                    self.current_colspan = int(attr_value)

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.in_cell = False
            self.current_row.append(
                (self.current_cell.strip(), self.current_rowspan, self.current_colspan)
            )
        elif tag == 'tr':
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data
```

### Requirement: 将 HTML 解析结果展开为完整二维矩阵

新增 `_expand_html_table` 方法，将 HTML 解析的稀疏表示展开为包含 `PdfCell` 和 `None` 占位的完整二维矩阵：

```python
@staticmethod
def _expand_html_table(parsed_rows):
    """将 HTML 解析的 (text, rowspan, colspan) 行展开为完整二维矩阵

    Returns:
        list[list[PdfCell | None]]: 展开后的矩阵，合并起始位置为 PdfCell，
                                     被合并位置为 None
    """
    if not parsed_rows:
        return []

    # 计算实际列数（考虑 colspan）
    n_cols = 0
    for row in parsed_rows:
        col_count = 0
        for _, _, colspan in row:
            col_count += colspan
        n_cols = max(n_cols, col_count)

    n_rows = len(parsed_rows)
    # 占位矩阵：False=空，True=被合并位置
    occupied = [[False] * n_cols for _ in range(n_rows)]
    result = [[None] * n_cols for _ in range(n_rows)]

    for row_idx, row in enumerate(parsed_rows):
        col_idx = 0
        for text, rowspan, colspan in row:
            # 跳过已被合并的位置
            while col_idx < n_cols and occupied[row_idx][col_idx]:
                col_idx += 1
            if col_idx >= n_cols:
                break

            # 创建 PdfCell（bbox 后续由 _compute_table_grid 设置）
            cell = PdfCell(
                text=text,
                bbox=(0, 0, 0, 0),
                row_idx=row_idx,
                col_idx=col_idx
            )
            cell.row_span = rowspan
            cell.col_span = colspan
            result[row_idx][col_idx] = cell

            # 标记被合并的位置
            for dr in range(rowspan):
                for dc in range(colspan):
                    r, c = row_idx + dr, col_idx + dc
                    if r < n_rows and c < n_cols:
                        occupied[r][c] = True
                        if dr > 0 or dc > 0:
                            result[r][c] = None  # 被合并位置

            col_idx += colspan

    return result
```

### Requirement: _compute_table_grid 为合并单元格计算跨行跨列 bbox

修改 `_compute_table_grid`，在为单元格分配 bbox 时检查 `row_span`/`col_span`：

```python
for row_idx, row in enumerate(cells):
    grid_y1 = ty1 + sum(row_heights[:row_idx])
    grid_y2 = grid_y1 + row_heights[row_idx]

    for col_idx, cell in enumerate(row):
        grid_x1 = tx1 + sum(col_widths[:col_idx])
        grid_x2 = grid_x1 + col_widths[col_idx]

        if cell is None:
            # 被合并位置，设置单格 bbox（不会被绘制）
            continue

        row_span = getattr(cell, 'row_span', 1)
        col_span = getattr(cell, 'col_span', 1)

        if row_span > 1 or col_span > 1:
            # 合并单元格：bbox 覆盖多行多列
            span_y2 = grid_y1 + sum(row_heights[row_idx:row_idx + row_span])
            span_x2 = grid_x1 + sum(col_widths[col_idx:col_idx + col_span])
            cell.bbox = (grid_x1, grid_y1, span_x2, span_y2)
            cell.width = span_x2 - grid_x1
            cell.height = span_y2 - grid_y1
        else:
            cell.bbox = (grid_x1, grid_y1, grid_x2, grid_y2)
            cell.width = grid_x2 - grid_x1
            cell.height = grid_y2 - grid_y1
```

### Requirement: _draw_translated_table 跳过被合并位置并优化网格线

修改 `_draw_translated_table`：

1. **跳过被合并位置**：遍历单元格时，如果 `cell is None`，跳过背景和文本绘制
2. **网格线跳过合并单元格内部**：构建"线段遮挡表"，记录每条水平线/垂直线被哪些合并单元格遮挡，只绘制未被遮挡的线段

```python
# 构建遮挡信息
h_line_blocked = {}  # {(row_boundary_idx): [(col_start, col_end), ...]}
v_line_blocked = {}  # {(col_boundary_idx): [(row_start, row_end), ...]}

for row_idx, row in enumerate(table_cells):
    for col_idx, cell in enumerate(row):
        if cell is None:
            continue
        row_span = getattr(cell, 'row_span', 1)
        col_span = getattr(cell, 'col_span', 1)
        if row_span > 1:
            # 遮挡 row_idx 到 row_idx+row_span-1 之间的水平线
            for r in range(row_idx, row_idx + row_span - 1):
                if r not in h_line_blocked:
                    h_line_blocked[r] = []
                h_line_blocked[r].append((col_idx, col_idx + col_span - 1))
        if col_span > 1:
            # 遮挡 col_idx 到 col_idx+col_span-1 之间的垂直线
            for c in range(col_idx, col_idx + col_span - 1):
                if c not in v_line_blocked:
                    v_line_blocked[c] = []
                v_line_blocked[c].append((row_idx, row_idx + row_span - 1))

# 绘制水平线（跳过被遮挡的段）
for row_i in range(len(row_heights) - 1):
    line_y = table_y0 + sum(row_heights[:row_i + 1])
    blocked_ranges = h_line_blocked.get(row_i, [])
    # 将 [0, n_cols-1] 减去 blocked_ranges，绘制剩余段
    segments = _compute_visible_segments(0, len(col_widths) - 1, blocked_ranges)
    for seg_start, seg_end in segments:
        x_start = table_x0 + sum(col_widths[:seg_start])
        x_end = table_x0 + sum(col_widths[:seg_end + 1])
        page.draw_line(
            fitz.Point(x_start, line_y),
            fitz.Point(x_end, line_y),
            color=(0, 0, 0), width=0.5
        )

# 绘制垂直线（同理）
for col_j in range(len(col_widths) - 1):
    line_x = table_x0 + sum(col_widths[:col_j + 1])
    blocked_ranges = v_line_blocked.get(col_j, [])
    segments = _compute_visible_segments(0, len(row_heights) - 1, blocked_ranges)
    for seg_start, seg_end in segments:
        y_start = table_y0 + sum(row_heights[:seg_start])
        y_end = table_y0 + sum(row_heights[:seg_end + 1])
        page.draw_line(
            fitz.Point(line_x, y_start),
            fitz.Point(line_x, y_end),
            color=(0, 0, 0), width=0.5
        )
```

辅助函数 `_compute_visible_segments`：

```python
def _compute_visible_segments(full_start, full_end, blocked_ranges):
    """计算 [full_start, full_end] 中未被 blocked_ranges 遮挡的连续段

    Args:
        full_start: 完整范围起点（含）
        full_end: 完整范围终点（含）
        blocked_ranges: list of (start, end) 被遮挡的范围

    Returns:
        list of (seg_start, seg_end) 可见段
    """
    if not blocked_ranges:
        return [(full_start, full_end)]

    # 合并重叠的遮挡范围
    sorted_blocks = sorted(blocked_ranges, key=lambda x: x[0])
    merged = [sorted_blocks[0]]
    for start, end in sorted_blocks[1:]:
        if start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # 计算可见段
    segments = []
    current = full_start
    for block_start, block_end in merged:
        if current < block_start:
            segments.append((current, block_start - 1))
        current = max(current, block_end + 1)
    if current <= full_end:
        segments.append((current, full_end))

    return segments
```

## REMOVED Requirements

无
