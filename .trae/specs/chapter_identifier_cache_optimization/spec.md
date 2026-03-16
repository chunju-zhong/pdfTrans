# 章节识别器缓存优化 - 产品需求文档

## Overview
- **Summary**: 优化 ChapterIdentifier 类中的缓存使用逻辑，解决 extract_bookmarks 中调用 _reset_cache 后，associate_* 方法又重新构建缓存的性能问题。
- **Purpose**: 提高章节识别和关联的性能，减少重复计算，优化资源使用。
- **Target Users**: 开发人员和使用 PDF 翻译工具的用户。

## Goals
- 优化 ChapterIdentifier 类的缓存使用逻辑，避免不必要的缓存重建
- 提高章节关联操作的性能
- 确保缓存在适当的时机更新
- 保持代码的可读性和可维护性

## Non-Goals (Out of Scope)
- 改变章节识别的核心算法
- 修改章节关联的逻辑
- 影响其他模块的功能

## Background & Context
当前 ChapterIdentifier 类在 extract_bookmarks 方法中构建章节树并分配编号后，调用 _reset_cache 重置缓存。然后在 associate_text_blocks、associate_tables 和 associate_images 方法中，又会调用 _ensure_chapter_cache 重新构建缓存。这种设计导致了不必要的重复计算，影响了性能。

## Functional Requirements
- **FR-1**: 优化缓存使用逻辑，避免在 extract_bookmarks 后立即重置缓存
- **FR-2**: 确保缓存在章节信息发生变化时正确更新
- **FR-3**: 保持所有关联方法的功能不变

## Non-Functional Requirements
- **NFR-1**: 性能优化 - 减少重复计算，提高章节关联操作的速度
- **NFR-2**: 代码质量 - 保持代码的可读性和可维护性
- **NFR-3**: 兼容性 - 确保修改后的代码与现有代码兼容

## Constraints
- **Technical**: 保持与现有代码结构的兼容性
- **Dependencies**: 不依赖外部库的变更

## Assumptions
- 章节信息在 extract_bookmarks 后不会立即变化
- 缓存构建是一个相对耗时的操作
- 所有关联方法都需要使用相同的缓存数据

## Acceptance Criteria

### AC-1: 缓存使用优化
- **Given**: 调用 extract_bookmarks 方法后
- **When**: 调用 associate_* 方法
- **Then**: 不会重新构建缓存，而是使用已构建的缓存
- **Verification**: `programmatic`
- **Notes**: 可以通过日志或性能测试验证

### AC-2: 缓存更新机制
- **Given**: 章节信息发生变化（如重新提取书签）
- **When**: 再次调用 extract_bookmarks 方法
- **Then**: 缓存会被正确重置和重建
- **Verification**: `programmatic`

### AC-3: 功能保持不变
- **Given**: 使用修改后的 ChapterIdentifier 类
- **When**: 执行章节关联操作
- **Then**: 章节关联结果与修改前一致
- **Verification**: `programmatic`

### AC-4: 代码可读性
- **Given**: 查看修改后的代码
- **When**: 分析缓存使用逻辑
- **Then**: 代码逻辑清晰，易于理解
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要添加缓存状态的监控或日志？
- [ ] 是否需要考虑多线程场景下的缓存一致性？