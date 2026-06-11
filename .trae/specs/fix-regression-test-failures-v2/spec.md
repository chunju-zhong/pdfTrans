# 回归测试修复 Spec

## Why

回归测试发现4个失败用例和1个测试基础设施问题，需要修复以保持测试套件的可靠性。

## What Changes

- 修复 `test_system_profiler.py` 4个 tier 判断失败：测试用例未设置 `total_memory_gb`，导致 tier 全部基于默认值16GB计算为 `low`
- 修复 `test_simple_pdf_gen.py` 模块级代码导致 pytest 收集崩溃
- 修复6个测试函数返回 `bool` 而非 `None` 的 PytestReturnNotNoneWarning

## Impact

- Affected code: `tests/test_system_profiler.py`, `tests/test_simple_pdf_gen.py`, `tests/test_chapter_identifier_cache.py`, `tests/test_list_item_continuation.py`, `tests/test_semantic_merge_optimization.py`, `tests/test_table_text_in_glossary.py`, `tests/test_two_phase_merge.py`

## ADDED Requirements

### Requirement: test_system_profiler tier 测试设置正确的 total_memory_gb

系统 SHALL 在 `test_system_profiler.py` 的 tier 测试中设置与 `available_memory_gb` 匹配的 `total_memory_gb`，确保 `_determine_tier` 基于 `total_memory_gb` 的判断与测试预期一致。

#### Scenario: minimal tier
- **WHEN** `total_memory_gb=4.0, available_memory_gb=4.0, cpu_count=2, cpu_count_logical=4`
- **THEN** `calc.tier == 'minimal'`

#### Scenario: low tier
- **WHEN** `total_memory_gb=12.0, available_memory_gb=12.0, cpu_count=4, cpu_count_logical=8`
- **THEN** `calc.tier == 'low'`

#### Scenario: medium tier
- **WHEN** `total_memory_gb=24.0, available_memory_gb=24.0, cpu_count=8, cpu_count_logical=16`
- **THEN** `calc.tier == 'medium'`

#### Scenario: high tier
- **WHEN** `total_memory_gb=48.0, available_memory_gb=48.0, cpu_count=16, cpu_count_logical=32`
- **THEN** `calc.tier == 'high'`

### Requirement: test_simple_pdf_gen.py 不导致 pytest 崩溃

系统 SHALL 确保 `test_simple_pdf_gen.py` 不会在模块级执行 `sys.exit()`，避免 pytest 收集阶段崩溃。

### Requirement: 测试函数返回 None

系统 SHALL 确保所有 pytest 测试函数返回 `None`（使用 `assert` 代替 `return True/False`），消除 PytestReturnNotNoneWarning。

## MODIFIED Requirements

（无）

## REMOVED Requirements

（无）
