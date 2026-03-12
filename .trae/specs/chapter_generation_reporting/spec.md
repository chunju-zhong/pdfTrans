# PDF翻译工具 - 章节生成结果上报功能

## Overview
- **Summary**: 实现将章节Markdown生成结果（成功/失败）上报到前端的逻辑，使用户能够实时了解生成状态。
- **Purpose**: 解决当前章节生成结果无法反馈到前端的问题，提高用户体验和系统透明度。
- **Target Users**: 使用PDF翻译工具的用户，特别是处理长文档的用户。

## Goals
- 实现章节生成结果的上报机制
- 确保前端能够接收到章节生成的状态信息
- 提供清晰的错误信息，便于用户了解失败原因
- 保持与现有代码的兼容性

## Non-Goals (Out of Scope)
- 修改前端代码实现
- 改变章节生成的核心逻辑
- 优化其他翻译流程步骤

## Background & Context
- 当前实现中，章节生成的结果（成功/失败）只记录在日志中，没有上报到前端
- 用户无法实时了解章节生成的状态，特别是当生成失败时
- 项目中已经有任务状态更新的机制，可以利用现有的状态更新接口

## Functional Requirements
- **FR-1**: 定义新的结果类用于 `generate_markdown` 返回汇总的处理结果（包括单 Markdown 和章节 Markdown）
- **FR-2**: 实现章节生成结果的上报机制，包括成功/失败信息
- **FR-3**: 汇总 MarkdownResult 中的截断警告
- **FR-4**: 确保前端能够接收到章节生成的状态信息
- **FR-5**: 提供清晰的错误信息，便于用户了解失败原因
- **FR-6**: 保持与现有代码的兼容性

## Non-Functional Requirements
- **NFR-1**: 确保上报机制的可靠性和实时性
- **NFR-2**: 保持代码的可维护性和可读性
- **NFR-3**: 确保与现有任务状态更新机制的一致性

## Constraints
- **Technical**: 使用现有的任务状态更新机制
- **Dependencies**: 依赖于现有的任务对象和状态更新接口

## Assumptions
- 任务对象具有状态更新的方法
- 前端能够处理并显示章节生成的状态信息

## Acceptance Criteria

### AC-1: 章节生成结果上报功能实现
- **Given**: 一个包含多个章节的PDF文档
- **When**: 执行按章节生成Markdown操作
- **Then**: 章节生成的结果（成功/失败）被上报到前端
- **Verification**: `programmatic`

### AC-2: 错误信息清晰可见
- **Given**: 章节生成失败
- **When**: 查看前端状态
- **Then**: 前端显示清晰的错误信息，说明失败原因
- **Verification**: `human-judgment`

### AC-3: 与现有代码兼容
- **Given**: 执行按章节生成Markdown操作
- **When**: 检查系统行为
- **Then**: 系统行为与之前保持一致，只是增加了结果上报功能
- **Verification**: `programmatic`

## Open Questions
- [x] 任务对象是否具有添加警告或错误信息的方法？
  - 是的，任务对象具有 `add_warning` 方法，可以用来添加警告信息
  - 警告信息会被包含在任务的 `warnings` 列表中，前端可以通过 `to_dict` 方法获取到这些信息