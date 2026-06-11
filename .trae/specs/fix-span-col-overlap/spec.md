# 修复 col_span 向右扫描误归上方 row_span 的 None Spec

## Why

`compute_span_from_none_positions` 向右扫描 col_span 时只检查 `bbox_matrix[row_idx][c]` 是否为 None，没有验证该 None 是否属于上方合并单元格的 row_span。当同一列有 row_span>1 的合并单元格时，其下方行的 None 会被误归为同行左侧单元格的 col_span。

例如第20页表格：
```
Row 3: | Top-K | 40 | Top-P(row_span=3) | 0.8(row_span=3) |
Row 4: | 提示词 | 将电影评论... | None | None |
Row 5: | 输出 | ```{... | None | None |
```
(4,2) 和 (4,3) 的 None 属于 (3,2) 和 (3,3) 的 row_span=3，但向右扫描时被误归为 (4,1) 的 col_span=3，导致 (4,1) 的 v_line_blocked 范围错误扩大。

## What Changes

- 修改 `compute_span_from_none_positions`：向右扫描 col_span 时，验证整列段（从 row_idx 到 row_idx+row_span-1）均为 None

## Impact

- Affected specs: `fix-span-computation-overlap`
- Affected code: `modules/extractors/coordinate_utils.py`

## ADDED Requirements

### Requirement: 向右扫描验证整列段为 None

向右扫描 col_span 时 SHALL 验证从 row_idx 到 row_idx+row_span-1 的所有位置均为 None，确保该列确实被当前合并单元格覆盖。

#### Scenario: 上方 row_span 产生的 None 不被误归为 col_span

- **WHEN** (3,2) row_span=3，(4,2) 和 (5,2) 为 None
- **AND** 扫描 (4,1) 向右时遇到 (4,2) 为 None
- **THEN** (4,1) 的 col_span 应为 1（因为 (4,2) 的 None 属于 (3,2) 的 row_span，不是 (4,1) 的 col_span）
- **AND** 只有 (4,1) 到 (4,1+col_span-1) 下方行段全为 None 时，col_span 才应增加

#### Scenario: 真正的 col_span 正常检测

- **WHEN** (0,1) col_span=3，(0,2) 和 (0,3) 为 None
- **AND** (0,2) 和 (0,3) 下方没有 row_span 产生的 None
- **THEN** (0,1) 的 col_span=3

## MODIFIED Requirements

### Requirement: compute_span_from_none_positions 向右扫描使用列段验证

修改向右扫描逻辑，先确定 row_span，再向右扫描时验证整列段均为 None：

```python
# 先确定 row_span（向下扫描，验证整行段均为 None）
row_span = 1
r = row_idx + 1
while r < num_rows:
    all_none = True
    for dc in range(col_span):  # col_span 此时为 1
        c = col_idx + dc
        if r >= len(bbox_matrix) or c >= len(bbox_matrix[r]) or bbox_matrix[r][c] is not None:
            all_none = False
            break
    if not all_none:
        break
    row_span += 1
    r += 1

# 再确定 col_span（向右扫描，验证整列段均为 None）
col_span = 1
c = col_idx + 1
while c < num_cols:
    all_none = True
    for dr in range(row_span):
        r = row_idx + dr
        if r >= len(bbox_matrix) or c >= len(bbox_matrix[r]) or bbox_matrix[r][c] is not None:
            all_none = False
            break
    if not all_none:
        break
    col_span += 1
    c += 1

# 验证：确认 col_span 扩大后，row_span 仍然有效
# 需要重新验证扩大后的矩形区域全为 None
```

但上述方法仍有问题：先确定 row_span 再确定 col_span 后，需要重新验证扩大后的矩形区域。

**最终方案**：使用迭代验证——先确定初始 row_span（col_span=1），再确定 col_span（基于 row_span），再重新验证 row_span（基于新 col_span），直到收敛。

```python
# 迭代确定 row_span 和 col_span
row_span = 1
col_span = 1

# 先确定 col_span=1 时的 row_span
r = row_idx + 1
while r < num_rows:
    if r >= len(bbox_matrix) or col_idx >= len(bbox_matrix[r]) or bbox_matrix[r][col_idx] is not None:
        break
    row_span += 1
    r += 1

# 基于 row_span 确定 col_span
c = col_idx + 1
while c < num_cols:
    all_none = True
    for dr in range(row_span):
        r = row_idx + dr
        if r >= len(bbox_matrix) or c >= len(bbox_matrix[r]) or bbox_matrix[r][c] is not None:
            all_none = False
            break
    if not all_none:
        break
    col_span += 1
    c += 1

# 基于 col_span 重新验证 row_span
while row_span > 1:
    all_none = True
    for dc in range(col_span):
        c = col_idx + dc
        r = row_idx + row_span - 1
        if r >= len(bbox_matrix) or c >= len(bbox_matrix[r]) or bbox_matrix[r][c] is not None:
            all_none = False
            break
    if all_none:
        break
    row_span -= 1
```

## REMOVED Requirements

无
