# Tasks

- [x] Task 1: 恢复 `split_translated_result` 为原有按比例拆分逻辑
  - 删除辅助函数 `_split_by_newlines`、`_split_by_newlines_and_ratio`、`_split_with_excess_newlines`、`_split_by_ratio`
  - 恢复 `split_translated_result` 函数体为内联实现（基于 HEAD 版本）
  - 保留 `_get_original_text_len` 函数（该函数在改版前后都存在）

- [x] Task 2: 删除 `tests/test_split_by_newline.py` 测试文件

- [x] Task 3: 更新 CHANGELOG 文档
  - 从 `docs/CHANGELOG.zh.md` 删除"拆分算法优化——以换行符为分隔点拆分翻译结果"相关条目
  - 从 `docs/CHANGELOG.md` 删除对应的英文条目
  - 更新关于 `_is_title_text` 和 `_clean_title_newlines` 的条目

- [x] Task 4: 删除 `modules/pdf_extractor.py` 中的 `_is_title_text` 和 `_clean_title_newlines`

# Task Dependencies

- 所有任务无依赖关系，可并行执行
