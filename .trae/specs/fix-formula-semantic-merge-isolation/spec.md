# 公式块语义合并保护 Spec

## Why
语义合并算法（`merge_semantic_blocks`、`merge_semantic_blocks_with_llm`、`merge_semantic_blocks_with_llm_two_phase`）从未检查 `is_formula` 属性，导致公式块（LaTeX文本）被当作普通文本与相邻文本块合并成一个 MergedBlock。合并后，`translate_merged_block` 检测到合并块中包含公式块时会跳过整个合并块的翻译，导致公式旁边的正常文本也被跳过翻译。

## What Changes
- 在 `merge_semantic_blocks` 中添加公式块隔离逻辑：公式块不与文本块合并，单独成块
- 在 `merge_semantic_blocks_with_llm` 中添加公式块隔离逻辑
- 在 `merge_semantic_blocks_with_llm_two_phase` 中添加公式块隔离逻辑
- 公式块之间也不互相合并（每个公式独立成块）

## Impact
- Affected code: `utils/text_processing.py`
- Affected specs: 无

## ADDED Requirements

### Requirement: 语义合并算法隔离公式块
系统 SHALL 在语义合并算法中检查 `is_formula` 属性，公式块不与任何其他块合并，单独成为一个 MergedBlock。

#### Scenario: 公式块与文本块相邻
- **WHEN** 公式块与文本块在垂直位置上相邻
- **THEN** 公式块不与文本块合并，公式块单独成为一个 MergedBlock
- **AND** 文本块根据正常合并规则处理

#### Scenario: 两个公式块相邻
- **WHEN** 两个公式块在垂直位置上相邻
- **THEN** 两个公式块不互相合并，各自独立成为 MergedBlock

#### Scenario: 无公式块的页面
- **WHEN** 页面中没有公式块
- **THEN** 合并逻辑与修改前完全一致，不受影响

## MODIFIED Requirements

### Requirement: merge_semantic_blocks 合并条件
在 `should_end_current_block` 判断之前，增加公式块检查：
- 如果当前块是公式块（`is_formula=True`），结束当前合并块，公式块单独成块
- 如果当前合并块的第一个原始块是公式块，结束当前合并块，当前块开始新的合并块

### Requirement: merge_semantic_blocks_with_llm 合并条件
与 `merge_semantic_blocks` 相同的公式块隔离逻辑。

### Requirement: merge_semantic_blocks_with_llm_two_phase 合并条件
与 `merge_semantic_blocks` 相同的公式块隔离逻辑。

## REMOVED Requirements

无
