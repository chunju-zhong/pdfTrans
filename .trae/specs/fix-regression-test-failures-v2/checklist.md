# Checklist

## test_system_profiler tier 修复

- [x] `test_minimal_tier` 设置 `total_memory_gb=4.0`，tier 为 `minimal`
- [x] `test_low_tier` 设置 `total_memory_gb=12.0`，tier 为 `low`
- [x] `test_medium_tier` 设置 `total_memory_gb=24.0`，tier 为 `medium`
- [x] `test_high_tier` 设置 `total_memory_gb=48.0`，tier 为 `high`
- [x] `test_high_load_reduces_params` 设置 `total_memory_gb=24.0`，高负载时线程数减少

## test_simple_pdf_gen 修复

- [x] `pytest` 收集阶段不再因 `test_simple_pdf_gen.py` 崩溃

## PytestReturnNotNoneWarning 修复

- [x] `test_chapter_identifier_cache.py::test_cache_optimization` 返回 None
- [x] `test_list_item_continuation.py::test_list_item_continuation` 返回 None
- [x] `test_semantic_merge_optimization.py::test_semantic_merge_optimization` 返回 None
- [x] `test_table_text_in_glossary.py::test_glossary_service_import` 返回 None
- [x] `test_two_phase_merge.py` 6个测试返回 None
- [x] 运行 `pytest` 无 PytestReturnNotNoneWarning
