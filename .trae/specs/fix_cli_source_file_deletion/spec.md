# 修复CLI模式下源文件被删除的问题

## Overview
- **Summary**: 修复PDF翻译工具在CLI模式下执行翻译命令时，源文件被错误删除且没有生成翻译结果的问题
- **Purpose**: 确保CLI模式下用户的原始PDF文件不会被删除，同时保证翻译失败时也不会丢失源文件
- **Target Users**: 使用CLI命令行界面的用户

## Goals
- 修复CLI模式下源文件被删除的问题
- 确保翻译失败时源文件保持完整
- 保持Web模式下的正常工作流程

## Non-Goals (Out of Scope)
- 不修改Web模式的文件处理逻辑
- 不改变翻译核心功能
- 不影响其他CLI功能

## Background & Context
- 当前实现中，`_complete_task` 方法无论翻译是否成功都会删除源文件
- CLI模式下，输入文件是用户的原始文件，不应被删除
- 只有Web模式下的临时上传文件才需要清理

## Functional Requirements
- **FR-1**: CLI模式下不应删除用户提供的源文件
- **FR-2**: Web模式下应继续清理临时上传的文件
- **FR-3**: 翻译失败时不应删除源文件
- **FR-4**: 翻译成功时应正确生成输出文件

## Non-Functional Requirements
- **NFR-1**: 修复不应影响Web模式的正常功能
- **NFR-2**: 修复应保持代码的可维护性
- **NFR-3**: 修复应兼容现有的API调用

## Constraints
- **Technical**: 需要区分CLI模式和Web模式
- **Business**: 确保用户体验不受影响

## Assumptions
- Web模式下的文件处理逻辑是正确的
- CLI模式下用户期望源文件保持不变

## Acceptance Criteria

### AC-1: CLI模式不删除源文件
- **Given**: 用户通过CLI执行翻译命令
- **When**: 翻译完成或失败
- **Then**: 源文件应保持完整，不被删除
- **Verification**: `programmatic`

### AC-2: Web模式继续清理临时文件
- **Given**: 用户通过Web界面上传文件并执行翻译
- **When**: 翻译完成
- **Then**: 临时上传的文件应被清理
- **Verification**: `programmatic`

### AC-3: 翻译失败时不删除源文件
- **Given**: 用户执行翻译命令但翻译失败
- **When**: 系统处理失败情况
- **Then**: 源文件应保持完整，不被删除
- **Verification**: `programmatic`

### AC-4: 翻译成功时生成输出文件
- **Given**: 用户执行翻译命令且翻译成功
- **When**: 系统完成翻译
- **Then**: 应生成正确的输出文件
- **Verification**: `programmatic`

## Open Questions
- [ ] 如何在 `_complete_task` 方法中区分CLI模式和Web模式？
- [ ] 如何处理异常情况下的文件清理？
