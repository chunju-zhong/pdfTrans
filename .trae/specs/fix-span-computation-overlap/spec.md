# 修复 span 计算中重叠 None 误判 Spec

## Why

`compute_span_from_none_positions` 向下扫描 row_span 时只检查 `bbox_matrix[r][col_idx]` 是否为 None，没有验证该 None 是否属于当前单元格的合并区域。当同行有多个合并单元格时，相邻合并单元格的 None 会被误归为当前单元格的 row_span，导致网格线被错误遮挡。

## What Changes

- 修改 `compute_span_from_none_positions`：向下扫描时，验证整行段（col_idx 到 col_idx+col_span-1）均为 None，而非仅检查 col_idx 位置

## Impact

- Affected specs: `fix-merged-cell-line-missing`
- Affected code: `modules/extractors/coordinate_utils.py`

## ADDED Requirements

### Requirement: 向下扫描验证整行段为 None

向下扫描 row_span 时 SHALL 验证从 col_idx 到 col_idx+col_span-1 的所有位置均为 None，确保该行确实被当前合并单元格覆盖。

#### Scenario: 相邻合并单元格的 None 不被误归

- **WHEN** 单元格 A(4,0) 的 row_span=2，单元格 B(4,1) 的 col_span=2
- **AND** (5,0) 和 (5,1) 均为 None
- **THEN** B 的 row_span 应为 1（因为 (5,1) 的 None 属于 A 的 row_span，不是 B 的）
- **AND** 只有 (5,0) 到 (5,0+col_span_B-1) 全为 None 时，B 的 row_span 才应增加

#### Scenario: 单个合并单元格正常检测

- **WHEN** 单元格 C(2,0) 的 row_span=2, col_span=3
- **AND** (3,0), (3,1), (3,2) 均为 None
- **THEN** C 的 row_span=2, col_span=3

## MODIFIED Requirements

### Requirement: compute_span_from_none_positions 使用行段验证

修改向下扫描逻辑：

```python
# 向下扫描，验证整行段均为 None
row_span = 1
r = row_idx + 1
while r < num_rows:
    # 检查从 col_idx 到 col_idx+col_span-1 的所有位置是否均为 None
    all_none = True
    for dc in range(col_span):
        c = col_idx + dc
        if r >= len(bbox_matrix) or c >= len(bbox_matrix[r]) or bbox_matrix[r][c] is not None:
            all_none = False
            break
    if not all_none:
        break
    row_span += 1
    r += 1
```

## REMOVED Requirements

无
