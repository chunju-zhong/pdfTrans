# PDF翻译工具 - 修复CLI输出文件后缀处理问题

## Overview
- **Summary**: 修复CLI模式下用户需要手动指定正确文件后缀的问题，实现智能后缀处理功能
- **Purpose**: 提高用户体验，使用户无需记住不同输出格式对应的文件后缀
- **Target Users**: 使用CLI模式的PDF翻译工具用户

## Goals
- 实现智能后缀处理，根据输出格式自动添加正确的文件后缀
- 保持向后兼容，对于已指定正确后缀的情况不做修改
- 支持所有输出格式：PDF、Word、Markdown

## Non-Goals (Out of Scope)
- 修改Web界面的文件处理逻辑
- 改变现有输出文件的生成方式
- 添加新的输出格式

## Background & Context
- 当前用户在使用CLI模式时，需要手动指定正确的文件后缀：
  - Markdown格式需要指定`.zip`后缀
  - PDF格式需要指定`.pdf`后缀
  - Word格式需要指定`.docx`后缀
- 这给用户带来了不便，容易因为后缀错误导致文件无法正确打开

## Functional Requirements
- **FR-1**: 系统应根据输出格式自动为用户指定的输出路径添加正确的文件后缀
- **FR-2**: 对于已指定正确后缀的情况，系统应保持不变
- **FR-3**: 支持所有输出格式的智能后缀处理

## Non-Functional Requirements
- **NFR-1**: 智能后缀处理应在用户指定输出路径时自动执行
- **NFR-2**: 处理逻辑应简洁高效，不影响整体翻译性能
- **NFR-3**: 应保持向后兼容，不破坏现有功能

## Constraints
- **Technical**: 仅修改CLI相关代码，不影响Web界面
- **Dependencies**: 依赖现有的文件处理逻辑

## Assumptions
- 用户可能会指定各种格式的输出路径，包括无后缀、错误后缀等情况
- 系统应能正确识别并处理这些情况

## Acceptance Criteria

### AC-1: Markdown格式自动添加.zip后缀
- **Given**: 用户指定输出路径为`output`，输出格式为`markdown`
- **When**: 执行翻译命令
- **Then**: 系统应自动将输出路径处理为`output.zip`
- **Verification**: `programmatic`

### AC-2: PDF格式自动添加.pdf后缀
- **Given**: 用户指定输出路径为`output`，输出格式为`pdf`
- **When**: 执行翻译命令
- **Then**: 系统应自动将输出路径处理为`output.pdf`
- **Verification**: `programmatic`

### AC-3: Word格式自动添加.docx后缀
- **Given**: 用户指定输出路径为`output`，输出格式为`docx`
- **When**: 执行翻译命令
- **Then**: 系统应自动将输出路径处理为`output.docx`
- **Verification**: `programmatic`

### AC-4: 已指定正确后缀时保持不变
- **Given**: 用户指定输出路径为`output.zip`，输出格式为`markdown`
- **When**: 执行翻译命令
- **Then**: 系统应保持输出路径为`output.zip`不变
- **Verification**: `programmatic`

## Open Questions
- [x] 如何处理用户指定了错误后缀的情况？（系统会自动替换为正确的后缀）
- [x] 是否需要在帮助文档中说明智能后缀处理功能？（是的，建议在文档中说明）