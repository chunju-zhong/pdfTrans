# 修复失败测试用例规格文档

## 问题概述

回归测试中发现12个失败的测试用例，分为三类问题：

### 问题1: test_title_body_separation.py (5个失败)
- **原因**: 语义合并逻辑问题，标题和正文被错误地合并到一起
- **建议**: 需要检查 `merge_semantic_blocks` 函数的逻辑，确保标题块不与正文块合并

### 问题2: test_title_position_fix.py (6个失败) - 已修复 ✅
- **原因**: 测试用例调用了已重命名的私有方法 `_find_title_position` → `_locate_title_blocks`
- **解决方案**: 同步更新测试用例中的方法名，并修复 MockPage 类支持 `flags` 参数

### 问题3: test_pdf_page_translation.py (1个失败)
- **原因**: 测试断言与实际行为不匹配
- **建议**: 检查 `process_translation` 函数的异常处理逻辑

## What Changes

### 1. test_title_position_fix.py 修复 (已完成)
- 将测试用例中的 `_find_title_position` 替换为 `_locate_title_blocks`
- 修复 MockPage 类，使其支持 `flags` 参数
- 测试结果：6个测试全部通过 ✅

## Impact
- Affected code:
  - `tests/test_title_position_fix.py` - 已修复

## ADDED Requirements

### Requirement: 修复 test_title_position_fix.py
同步测试用例中的方法名。

#### Scenario: 方法名同步
- **GIVEN** test_title_position_fix.py 测试用例
- **WHEN** 调用 _find_title_position 方法
- **THEN** 替换为 _locate_title_blocks

## Acceptance Criteria

### AC-1: test_title_position_fix.py 全部通过 ✅
- **WHEN** 运行测试
- **THEN** 6个失败用例全部通过
