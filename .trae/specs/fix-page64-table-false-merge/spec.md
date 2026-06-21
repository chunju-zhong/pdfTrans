# 修复第64页表格单元格误合并 Spec

## Why
第64页表格在输出PDF中有很多单元格被错误合并。根因是 `compute_span_from_none_positions` 将 `bbox_matrix` 中所有 `None` 都视为合并单元格的被覆盖位置，但 PyMuPDF 对空单元格（无文本、边框检测不完美）也会返回 `None`，导致相邻有内容的单元格被误判为跨行/跨列合并。

具体问题链：
1. PyMuPDF `table.rows` 对某些空单元格返回 `None`（非合并原因，而是检测失败）
2. `_build_bbox_matrix` 对短行用 `None` 填充，也被误判为合并位置
3. `compute_span_from_none_positions` 无几何验证：不检查起始单元格的 bbox 是否真正跨越了推断的 span 区域
4. 结果：一个普通单元格右侧若有空单元格（`None`），会被判定为 `col_span > 1`，吞并空单元格

## What Changes
- 在 `compute_span_from_none_positions` 中增加几何验证：推断的 span 必须与起始单元格的 bbox 尺寸一致，否则不合并
- 在 `table_processor.py` 中增加日志：记录每个推断的 span 及其几何验证结果

## Impact
- Affected code: `modules/extractors/coordinate_utils.py` 中的 `compute_span_from_none_positions` 函数（第142-252行）
- Affected code: `modules/extractors/table_processor.py` 中的表格构建逻辑（第430-503行）
- 影响范围：所有 PyMuPDF 提取路径的表格

## ADDED Requirements

### Requirement: 合并单元格 span 推断必须通过几何验证
`compute_span_from_none_positions` 推断的 span SHALL 通过几何验证才生效。

#### Scenario: 起始单元格 bbox 覆盖推断的 span 区域
- **WHEN** 推断某单元格 (row_idx, col_idx) 的 span 为 (row_span, col_span)
- **AND** 该单元格的 bbox 高度 >= 覆盖行数的 80%，宽度 >= 覆盖列数的 80%
- **THEN** 该 span 有效，加入 span_map

#### Scenario: 起始单元格 bbox 不覆盖推断的 span 区域（空单元格导致的误判）
- **WHEN** 推断某单元格 (row_idx, col_idx) 的 span 为 (row_span, col_span)
- **AND** 该单元格的 bbox 高度 < 覆盖行数的 80%，或宽度 < 覆盖列数的 80%
- **THEN** 该 span 无效，不加入 span_map，该单元格保持 row_span=1, col_span=1

#### Scenario: bbox_matrix 中有 None 但无有效 span
- **WHEN** `compute_span_from_none_positions` 返回空 span_map，但 bbox_matrix 中有 None
- **THEN** 这些 None 位置应视为空单元格（无文本），而非合并位置
- **AND** 在 table_processor.py 中为这些空单元格创建空的 PdfCell（text=""），而非跳过

### Requirement: 空单元格（bbox 为 None）创建空 PdfCell
当 `bbox_matrix` 中某位置为 `None` 且不在 span_map 的覆盖范围内时，SHALL 创建一个空的 PdfCell 而非跳过。

#### Scenario: None 位置不在任何合并范围内
- **WHEN** 遍历 data 时，某位置 (row_idx, col_idx) 在 bbox_matrix 中为 None
- **AND** 该位置不在任何有效 span 的覆盖范围内
- **THEN** 使用均匀分割计算该位置的 bbox，创建 text="" 的 PdfCell

#### Scenario: None 位置在有效合并范围内
- **WHEN** 遍历 data 时，某位置在 bbox_matrix 中为 None
- **AND** 该位置在某个有效 span 的覆盖范围内
- **THEN** 跳过该位置（当前行为不变）

### Requirement: 合并单元格推断日志增强
系统 SHALL 在合并单元格推断时记录几何验证结果。

#### Scenario: span 推断通过几何验证
- **WHEN** 推断的 span 通过几何验证
- **THEN** 日志记录：单元格坐标、span 值、bbox 尺寸、覆盖区域尺寸、验证通过

#### Scenario: span 推断未通过几何验证
- **WHEN** 推断的 span 未通过几何验证
- **THEN** 日志记录：单元格坐标、推断的 span 值、bbox 尺寸、覆盖区域尺寸、验证失败原因

## MODIFIED Requirements

### Requirement: compute_span_from_none_positions 返回值
返回值从 `dict: {(row_idx, col_idx): (row_span, col_span)}` 修改为 `dict: {(row_idx, col_idx): (row_span, col_span)}`，但仅包含通过几何验证的 span。未通过验证的推断不包含在返回值中。

### Requirement: table_processor.py 中 None 位置的处理
原有逻辑（bbox_matrix 中 None 位置一律跳过）修改为：检查 None 位置是否在有效 span 覆盖范围内，不在范围内的创建空 PdfCell。
