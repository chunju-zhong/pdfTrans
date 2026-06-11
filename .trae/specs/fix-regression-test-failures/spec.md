# 修复回归测试失败 Spec

## Why

回归测试中有 31 个测试失败，原因是代码重构后测试未同步更新。需要将测试适配到当前代码接口，确保回归测试套件可正常通过。

## What Changes

按 6 大根因分组修复测试：

1. **`_degrade_params` 降级逻辑**：在 `_degrade_params` 中根据 `attempt` 设置 `skip_table`/`skip_formula`，并统一降级策略
2. **`handle_same_language` 已有意删除**：删除 `test_same_language_optimization.py` 中对应的测试用例
3. **`NON_BODY_LABELS` 缺少 `header`**：将 `header` 加入 `NON_BODY_LABELS`
4. **`_create_pipeline` 单管线架构**：更新 `test_ocr_extractor.py` 的 mock 策略
5. **`merge_semantic_blocks` 返回 MergedBlock 对象**：修复测试中的字典访问为属性访问
6. **`process_translation` 签名变更**：更新集成测试的参数和 mock 链条

## Impact

- Affected code:
  - `modules/ocr/ocr_worker.py` — `_degrade_params` 增加 skip 降级逻辑
  - `modules/ocr/paddle_extractor.py` — `NON_BODY_LABELS` 增加 `header`
  - `modules/ocr/system_profiler.py` — 修正 tier 边界值
  - `tests/test_same_language_optimization.py` — 删除（功能已有意移除）
  - `tests/test_ocr_extractor.py` — 更新 mock 策略
  - `tests/test_ocr_worker.py` — 适配新降级逻辑
  - `tests/test_semantic_merge.py` — 修复属性访问
  - `tests/test_semantic_merge_extended.py` — 修复属性访问 + 删除重复方法
  - `tests/test_title_body_separation.py` — 适配新合并逻辑
  - `tests/test_translation_service.py` — 更新参数和 mock
  - `tests/test_pdf_page_translation.py` — 更新参数和 mock
  - `tests/test_pdf_extractor.py` — 适配签名变更
  - `tests/test_system_profiler.py` — 修正边界值

## ADDED Requirements

### Requirement: `_degrade_params` 根据 attempt 设置 skip_table/skip_formula

`_degrade_params` SHALL 根据重试次数递进跳过功能：
- `attempt=0`：`skip_table=False`, `skip_formula=False`
- `attempt=1`：`skip_table=True`, `skip_formula=False`
- `attempt≥2`：`skip_table=True`, `skip_formula=True`

### Requirement: `NON_BODY_LABELS` 包含 `header`

`NON_BODY_LABELS` SHALL 包含 `header`，使页眉文本块的 `is_body_text = False`。

## MODIFIED Requirements

### Requirement: 删除同语言优化测试

`test_same_language_optimization.py` 中的测试 SHALL 被删除，因为 `handle_same_language` 方法已有意移除（参见 `remove-same-language-copy` spec）。

### Requirement: 测试适配当前代码接口

所有失败测试 SHALL 适配到当前代码的接口签名、返回类型和内部逻辑，使测试能正确验证功能。

## REMOVED Requirements

无
