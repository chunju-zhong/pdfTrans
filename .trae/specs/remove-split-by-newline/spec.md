# 删除以换行符为分隔点拆分功能 Spec

## Why

以换行符为分隔点拆分翻译结果的功能效果不佳。当翻译结果包含换行符时，按换行符拆分会导致文本分配不合理（例如无换行符时第一个块获得全部内容、后续块为空），反而引入新的渲染问题。需要删除该功能，恢复原有的按比例拆分逻辑。

## What Changes

- **删除 4 个辅助函数**：`_split_by_newlines`、`_split_by_newlines_and_ratio`、`_split_with_excess_newlines`、`_split_by_ratio`
- **恢复 `split_translated_result`**：删除换行符检测逻辑（策略1-4分支），恢复为内联的按比例拆分实现（即 HEAD 版本）
- **删除测试文件**：`tests/test_split_by_newline.py`
- **更新 CHANGELOG**：删除"拆分算法优化——以换行符为分隔点拆分翻译结果"相关条目

## Impact

- Affected code: `utils/text_processing.py` 的 `split_translated_result` 函数及相关 4 个辅助函数
- Deleted test: `tests/test_split_by_newline.py`
- 行为变更：拆分算法恢复为纯按比例分配，不再以换行符为分隔点
- 涉及先前 spec：`split-by-newline-separators/`

## ADDED Requirements

（无新增需求）

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

### Requirement: 拆分算法优先以换行符为分隔点

**Reason**: 功能效果不佳，导致文本分配不合理
**Migration**: 恢复原有的按比例拆分逻辑
