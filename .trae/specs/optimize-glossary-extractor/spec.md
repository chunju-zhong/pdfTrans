# PDF翻译工具 - 术语提取器代码优化 PRD

## Overview
- **Summary**: 优化术语提取器代码质量，解决代码审查中发现的三个问题：函数过长、提示词规则重复、藏文术语对照表重复
- **Purpose**: 提高代码可读性、可维护性和可测试性，降低维护成本
- **Target Users**: 开发人员（维护和扩展术语提取功能）

## Goals
- 将 `extract_glossary()` 函数拆分为多个小方法，每个方法不超过50行
- 将重复的提示词规则提取为常量，减少维护成本
- 将藏文术语对照表提取为共享常量，确保翻译规则和术语提取规则使用一致的术语

## Non-Goals (Out of Scope)
- 不修改术语提取的业务逻辑和算法
- 不添加新功能或新语言支持
- 不修改其他模块的代码

## Background & Context
代码审查发现以下问题：
1. `modules/glossary_extractor.py` 中 `extract_glossary()` 函数约106行，违反50行限制
2. 提示词模板中多处重复相同规则（如"核心要求"重复5次以上）
3. `prompts/language_rules/bo_to_zh.py` 中术语对照表在翻译规则和术语提取规则中重复

## Functional Requirements
- **FR-1**: 将 `extract_glossary()` 函数拆分为 `_build_prompt()`、`_call_api()`、`_process_response()` 等小方法
- **FR-2**: 将重复的提示词规则提取为类常量或模块级常量
- **FR-3**: 将藏文术语对照表提取为共享常量，翻译规则和术语提取规则复用

## Non-Functional Requirements
- **NFR-1**: 每个函数不超过50行
- **NFR-2**: 保持代码符合PEP 8规范
- **NFR-3**: 所有现有测试必须通过

## Constraints
- **Technical**: Python 3.9+，保持与现有代码风格一致
- **Dependencies**: 不引入新的第三方库

## Assumptions
- 优化后的代码行为与原代码完全一致
- 现有的测试用例覆盖了主要功能

## Acceptance Criteria

### AC-1: extract_glossary() 函数拆分完成
- **Given**: `modules/glossary_extractor.py` 中 `extract_glossary()` 函数当前约106行
- **When**: 执行代码优化
- **Then**: `extract_glossary()` 函数不超过50行，提示词构建、API调用、响应处理分别提取为独立方法
- **Verification**: `programmatic`

### AC-2: 提示词规则去重完成
- **Given**: 提示词模板中存在重复规则（如"核心要求"重复5次以上）
- **When**: 执行代码优化
- **Then**: 重复规则提取为常量，提示词模板通过拼接常量构建，无重复文本
- **Verification**: `programmatic`

### AC-3: 藏文术语对照表去重完成
- **Given**: `prompts/language_rules/bo_to_zh.py` 中翻译规则和术语提取规则包含相同的术语对照表
- **When**: 执行代码优化
- **Then**: 术语对照表提取为共享常量，两个规则复用同一常量
- **Verification**: `programmatic`

### AC-4: 所有测试通过
- **Given**: 优化前测试全部通过
- **When**: 执行优化后运行测试
- **Then**: 所有测试继续通过，无回归
- **Verification**: `programmatic`

## Open Questions
- [ ] 无
