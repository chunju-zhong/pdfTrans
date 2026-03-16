# 章节识别器优化 - 产品需求文档

## Overview
- **Summary**: 优化章节识别器的标题定位逻辑，统一使用 `_find_title_position` 函数来查找标题对应的文本块，不再依赖从 PDF 书签的 dest 中提取位置信息。
- **Purpose**: 简化代码逻辑，提高标题识别的准确性和可靠性。
- **Target Users**: 开发人员和用户（通过更准确的章节识别间接受益）。

## Goals
- 统一标题定位逻辑，始终使用 `_find_title_position` 查找标题对应的文本块
- 为 `_find_title_position` 函数改一个更合适的名字
- 移除不再需要的 `_extract_position` 函数
- 保持代码的可读性和可维护性

## Non-Goals (Out of Scope)
- 改变章节识别的核心算法
- 影响其他模块的功能
- 改变章节树的构建逻辑

## Background & Context
当前的章节识别器有两种获取标题位置的方式：
1. 通过 `_extract_position` 从 PDF 书签的 dest 中提取位置
2. 如果没有位置信息，通过 `_find_title_position` 在页面中查找标题

这种双重逻辑增加了代码复杂度，且可能导致不一致的结果。统一使用 `_find_title_position` 可以简化逻辑，提高可靠性。

## Functional Requirements
- **FR-1**: 重命名 `_find_title_position` 为更合适的名字
- **FR-2**: 移除 `_extract_position` 函数
- **FR-3**: 修改 `_build_chapter_tree` 方法，始终调用 `_find_title_position` 来查找标题
- **FR-4**: 确保修改后章节识别功能正常工作

## Non-Functional Requirements
- **NFR-1**: 代码修改后保持向后兼容
- **NFR-2**: 代码可读性和可维护性不降低
- **NFR-3**: 章节识别的准确性不降低

## Constraints
- **Technical**: 基于 PyMuPDF 库的文本块提取功能
- **Dependencies**: 依赖 PyMuPDF 库的文本块提取功能

## Assumptions
- `_find_title_position` 函数能够准确找到标题对应的文本块
- 移除 `_extract_position` 不会影响章节识别的准确性

## Acceptance Criteria

### AC-1: 函数重命名
- **Given**: 代码修改前
- **When**: 执行函数重命名操作
- **Then**: `_find_title_position` 被重命名为更合适的名字，所有调用该函数的地方也相应更新
- **Verification**: `human-judgment`

### AC-2: 移除 _extract_position 函数
- **Given**: 代码修改前
- **When**: 移除 `_extract_position` 函数
- **Then**: 代码中不再存在 `_extract_position` 函数，所有调用该函数的地方都被修改
- **Verification**: `programmatic`

### AC-3: 统一标题定位逻辑
- **Given**: 代码修改前
- **When**: 修改 `_build_chapter_tree` 方法
- **Then**: 不再调用 `_extract_position`，始终调用重命名后的 `_find_title_position` 函数
- **Verification**: `programmatic`

### AC-4: 章节识别功能正常
- **Given**: 代码修改后
- **When**: 运行章节识别功能
- **Then**: 章节识别功能正常工作，能够准确找到章节标题
- **Verification**: `programmatic`

## Open Questions
- [ ] 什么名字最适合 `_find_title_position` 函数？
- [ ] 移除 `_extract_position` 后是否需要添加新的错误处理？