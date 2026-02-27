# Max Tokens Property Enhancement - Product Requirement Document

## Overview
- **Summary**: 将多个模块中的 `max_tokens` 参数设计为具有默认值的类属性，并支持在类外部进行设置，以便更灵活地控制API调用的token限制。
- **Purpose**: 解决当前代码中 `max_tokens` 硬编码的问题，提高代码的可配置性和可维护性。
- **Target Users**: 开发人员和系统管理员，需要根据不同场景调整token限制。

## Goals
- 将 `max_tokens` 从硬编码值改为具有默认值的类属性
- 支持在类外部设置 `max_tokens` 值
- 确保修改后的代码与现有功能完全兼容
- 提供清晰的文档说明如何设置和使用 `max_tokens` 属性

## Non-Goals (Out of Scope)
- 不改变现有的API调用逻辑
- 不修改其他参数的设置方式
- 不影响现有的翻译和语义分析功能

## Background & Context
- 当前代码中 `max_tokens` 是硬编码在API调用中的固定值
- 不同的模型和场景可能需要不同的token限制
- 硬编码的方式不够灵活，难以根据实际需求进行调整
- 语义分析器有两种不同的方法：单个语义分析和批量语义分析，后者需要处理更多的文本内容，因此需要更大的token限制

## Functional Requirements
- **FR-1**: 将 `aiping_semantic_analyzer.py` 中的 `max_tokens` 改为类属性，默认值为1024（用于单个语义分析）和2048（用于批量语义分析）
- **FR-2**: 将 `aiping_translator.py` 中的 `max_tokens` 改为类属性，默认值为8192
- **FR-3**: 将 `markdown_generator.py` 中的 `max_tokens` 改为类属性，默认值为8192
- **FR-4**: 将 `semantic_analyzer.py` 中的 `max_tokens` 改为类属性，默认值为1024（用于单个语义分析）和2048（用于批量语义分析）
- **FR-5**: 将 `silicon_flow_translator.py` 中的 `max_tokens` 改为类属性，默认值为8192

## Non-Functional Requirements
- **NFR-1**: 保持向后兼容性，默认值与当前硬编码值一致
- **NFR-2**: 代码修改应遵循现有的代码风格和规范
- **NFR-3**: 提供清晰的文档说明如何设置 `max_tokens` 属性

## Constraints
- **Technical**: 所有修改必须在现有代码结构的基础上进行，不引入新的依赖
- **Dependencies**: 依赖于现有的OpenAI客户端API结构

## Assumptions
- 所有模块都使用OpenAI客户端的 `max_tokens` 参数
- 修改后的代码应保持与现有测试的兼容性

## Acceptance Criteria

### AC-1: AipingSemanticAnalyzer max_tokens 属性
- **Given**: 实例化 AipingSemanticAnalyzer 类
- **When**: 未设置 max_tokens 属性
- **Then**: 应使用默认值1024和2048
- **Verification**: `programmatic`

### AC-2: AipingSemanticAnalyzer 外部设置 max_tokens
- **Given**: 实例化 AipingSemanticAnalyzer 类并设置 max_tokens 属性
- **When**: 调用 analyze_semantic_relationship 方法
- **Then**: 应使用设置的 max_tokens 值
- **Verification**: `programmatic`

### AC-3: AipingTranslator max_tokens 属性
- **Given**: 实例化 AipingTranslator 类
- **When**: 未设置 max_tokens 属性
- **Then**: 应使用默认值8192
- **Verification**: `programmatic`

### AC-4: AipingTranslator 外部设置 max_tokens
- **Given**: 实例化 AipingTranslator 类并设置 max_tokens 属性
- **When**: 调用 translate 方法
- **Then**: 应使用设置的 max_tokens 值
- **Verification**: `programmatic`

### AC-5: MarkdownGenerator max_tokens 属性
- **Given**: 实例化 MarkdownGenerator 类
- **When**: 未设置 max_tokens 属性
- **Then**: 应使用默认值8192
- **Verification**: `programmatic`

### AC-6: MarkdownGenerator 外部设置 max_tokens
- **Given**: 实例化 MarkdownGenerator 类并设置 max_tokens 属性
- **When**: 调用 generate_markdown 方法
- **Then**: 应使用设置的 max_tokens 值
- **Verification**: `programmatic`

### AC-7: SemanticAnalyzer max_tokens 属性
- **Given**: 实例化 SemanticAnalyzer 类
- **When**: 未设置 max_tokens 属性
- **Then**: 应使用默认值1024和2048
- **Verification**: `programmatic`

### AC-8: SemanticAnalyzer 外部设置 max_tokens
- **Given**: 实例化 SemanticAnalyzer 类并设置 max_tokens 属性
- **When**: 调用 analyze_semantic_relationship 方法
- **Then**: 应使用设置的 max_tokens 值
- **Verification**: `programmatic`

### AC-9: SiliconFlowTranslator max_tokens 属性
- **Given**: 实例化 SiliconFlowTranslator 类
- **When**: 未设置 max_tokens 属性
- **Then**: 应使用默认值8192
- **Verification**: `programmatic`

### AC-10: SiliconFlowTranslator 外部设置 max_tokens
- **Given**: 实例化 SiliconFlowTranslator 类并设置 max_tokens 属性
- **When**: 调用 translate 方法
- **Then**: 应使用设置的 max_tokens 值
- **Verification**: `programmatic`

## Open Questions
- [ ] 各个模块的 max_tokens 默认值是否需要统一？
- [ ] 是否需要在配置文件中统一管理这些默认值？