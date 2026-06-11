# 修复代码审查发现的4个问题 Spec

## Why
代码审查发现 `split_translated_result` 和 `pdf_generator` 中存在3个可修复的问题：负值保护缺失、行高循环估计偏差、O(n²) 性能问题，以及1个文档改进建议。

## What Changes
- `utils/text_processing.py`：修复 `max_allowed_end` 负值问题，优化 `sum(original_lengths[i:])` 为递减变量
- `modules/pdf_generator.py`：改进行高倍率估算方法，减少循环估计偏差
- `modules/extractors/text_analyzer.py`：为 `roman_to_int` 添加文档说明

## Impact
- Affected code: `utils/text_processing.py`, `modules/pdf_generator.py`, `modules/extractors/text_analyzer.py`
- 行为变更：行高估算更准确，`split_translated_result` 更健壮

## ADDED Requirements

### Requirement: max_allowed_end 负值保护

系统 SHALL 在 `split_translated_result()` 中确保 `max_allowed_end` 不小于 `start_pos`，避免负值导致逻辑混乱。

#### Scenario: 翻译文本非常短，min_chars × remaining_blocks > translation_len
- **WHEN** `translation_len = 5`, `min_characters_per_block = 3`, `remaining_blocks = 2`
- **THEN** `max_allowed_end = max(start_pos, translation_len - min_characters_per_block * remaining_blocks)`
- **AND** `max_allowed_end >= start_pos`

### Requirement: 行高倍率估算改进

系统 SHALL 使用迭代收敛方法计算行高倍率，而非单次循环估计。

#### Scenario: 原文行高倍率为1.5（CJK文本）
- **WHEN** bbox高度=54pt, 字体大小=12pt, 实际行数=3
- **THEN** 估算行高倍率应接近1.5，而非1.2

#### Scenario: 原文行高倍率为1.2（拉丁文本）
- **WHEN** bbox高度=43.2pt, 字体大小=12pt, 实际行数=3
- **THEN** 估算行高倍率应接近1.2

### Requirement: O(n) 比例分配

系统 SHALL 使用递减变量 `remaining_original_len` 替代 `sum(original_lengths[i:])`，使比例分配为 O(n)。

### Requirement: roman_to_int 文档说明

系统 SHALL 在 `roman_to_int` 函数文档中注明不验证罗马数字语法规则。
