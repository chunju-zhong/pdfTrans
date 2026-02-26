# PDF翻译工具 - Markdown生成器重构产品需求文档

## Overview
- **Summary**: 重构现有的MarkdownGenerator类，增加aiping和硅基流动派生类，使Markdown生成过程能够根据用户选择的翻译API使用不同的派生类，支持针对不同模型的个性化参数设置。
- **Purpose**: 实现Markdown生成过程中对不同翻译API的个性化参数支持，例如在aiping的extra_body中定义费用优先策略。
- **Target Users**: 使用PDF翻译工具的开发人员和最终用户。

## Goals
- 重构现有的MarkdownGenerator类，使用其成为沿用OpenAI接口模式的基类
- 创建AipingMarkdownGenerator派生类，支持aiping特定参数
- 实现工厂方法或创建函数，根据用户选择返回相应的生成器实例
- 确保重构后的代码符合项目的代码风格和结构规范

## Non-Goals (Out of Scope)
- 不修改Markdown生成的核心逻辑和功能
- 不改变现有的API接口和使用方式
- 不添加新的依赖库

## Background & Context
- 现有MarkdownGenerator类使用OpenAI客户端调用布局模型生成Markdown格式
- 不同的翻译API（如aiping、硅基流动）可能需要不同的参数设置
- 目前的实现无法针对不同的翻译API进行个性化参数配置

## Functional Requirements
- **FR-1**: 重构MarkdownGenerator类，使其成为基类
  - 保留核心功能和方法
  - 确保向后兼容性
  - 支持OpenAI，硅基流动等使用标准方法调用的平台

- **FR-2**: 创建AipingMarkdownGenerator派生类
  - 继承MarkdownGenerator基类
  - 支持aiping特定的参数设置
  - 在extra_body中定义费用优先策略

- **FR-3**: 实现工厂方法或创建函数
  - 根据用户选择的翻译API返回相应的生成器实例
  - 提供简单的接口供其他模块调用

## Non-Functional Requirements
- **NFR-1**: 代码质量
  - 遵循项目的代码风格规范
  - 保持代码可读性和可维护性
  - 适当添加文档字符串

- **NFR-2**: 性能
  - 重构后的代码性能应不低于原有实现
  - 避免不必要的开销

- **NFR-3**: 兼容性
  - 确保与现有代码的兼容性
  - 不破坏现有的功能

## Constraints
- **Technical**: 
  - Python 3.9+
  - 保持与现有依赖库的兼容性
  - 遵循项目的目录结构和模块划分

## Assumptions
- 现有的MarkdownGenerator类功能正常
- 不同翻译API的参数差异主要体现在API调用时的参数设置
- 工厂方法或创建函数将在需要时被其他模块调用

## Acceptance Criteria

### AC-1: 重构后的MarkdownGenerator基类功能正常
- **Given**: 现有代码使用MarkdownGenerator类
- **When**: 重构后继续使用相同的方式调用
- **Then**: 功能应与重构前保持一致
- **Verification**: `programmatic`

### AC-2: AipingMarkdownGenerator派生类支持费用优先策略
- **Given**: 使用AipingMarkdownGenerator生成Markdown
- **When**: 调用布局模型API
- **Then**: 应在extra_body中包含费用优先的设置
- **Verification**: `programmatic`

### AC-3: 工厂方法或创建函数能正确返回相应的生成器实例
- **Given**: 调用工厂方法并指定翻译API类型
- **When**: 传入不同的API类型
- **Then**: 应返回相应的生成器实例
- **Verification**: `programmatic`

### AC-4: 代码符合项目的代码风格和结构规范
- **Given**: 重构后的代码
- **When**: 进行代码审查
- **Then**: 应符合项目的代码风格和结构规范
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要在工厂方法中添加缓存机制，避免重复创建生成器实例？
- [ ] 除了费用优先策略外，aiping和硅基流动是否还有其他需要在Markdown生成过程中设置的特定参数？