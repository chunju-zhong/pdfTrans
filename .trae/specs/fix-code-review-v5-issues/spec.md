# 代码审查v5优化 Spec

## Why
代码审查发现2个HIGH级别和4个MEDIUM/LOW级别的代码质量问题，需要修复以提高代码可读性和健壮性。

## What Changes
- 移除`_compute_table_layout`中Step 1无用的`row_line_counts`变量
- 截断逻辑计数方式改为显式`attempts`计数器
- 恢复`_extract_json`第三级容错（首尾花括号匹配）
- `from __future__ import annotations`移至编码声明之后
- 多bbox拆分时单换行`\n`拆分后段落数不等于bbox数的fallback处理

## Impact
- Affected code: `modules/ocr/llm_extractor.py`, `modules/pdf_generator.py`

## ADDED Requirements

### Requirement: 截断逻辑使用显式计数器
截断逻辑SHALL使用显式`attempts`计数器替代索引差值间接计数，提高可读性。

#### Scenario: CJK截断计数
- **WHEN** CJK文本截断循环执行
- **THEN** 使用`attempts += 1; if attempts >= max_truncation_attempts: break`替代`(len(cell_text) - 1 - n) >= max_truncation_attempts`

#### Scenario: 英文截断计数
- **WHEN** 英文文本截断循环执行
- **THEN** 使用同样的显式计数器方式

### Requirement: 多bbox拆分段落数不匹配时的fallback
当多bbox场景下按换行拆分文本后段落数不等于bbox数时，SHALL将所有文本分配给第一个bbox（而非丢弃拆分结果）。

#### Scenario: 段落数小于bbox数
- **WHEN** 2个bbox但文本只有1个段落
- **THEN** 文本分配给第一个bbox，第二个bbox使用空文本

#### Scenario: 段落数大于bbox数
- **WHEN** 2个bbox但文本有3个段落
- **THEN** 前N-1个段落各自分配一个bbox，剩余段落合并到最后一个bbox

## MODIFIED Requirements

### Requirement: _extract_json三级容错
`_extract_json` SHALL恢复第三级容错：当直接解析和markdown代码块提取都失败时，尝试匹配第一个`{`和最后一个`}`之间的内容。

### Requirement: from __future__ import annotations位置
`from __future__ import annotations` SHALL位于`# -*- coding: utf-8 -*-`编码声明之后、其他import之前。

## REMOVED Requirements

### Requirement: Step 1中row_line_counts变量
**Reason**: Step 1中的`row_line_counts`在Step 4中被同名变量遮蔽，Step 1的值从未被使用，属于死代码。
**Migration**: 移除Step 1中的`row_line_counts = []`和`row_line_counts.append(max_lines)`。
