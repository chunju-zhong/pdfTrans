# PDF翻译工具 - 章节图片和表格位置修复 PRD

## Overview
- **Summary**: 修复按章节生成Markdown时图片和表格位置不正确的问题，确保图片和表格被正确插入到所在章节的正确位置。
- **Purpose**: 解决第三章图片被放到第四章的问题，以及图片位置不在正确文本块附近的问题。
- **Target Users**: 使用PDF翻译工具的用户，特别是需要按章节生成Markdown文档的用户。

## Goals
- 确保图片和表格被正确分配到它们所属的章节
- 确保图片和表格在章节Markdown中出现在正确的文本块附近
- 保持与完整Markdown输出逻辑的一致性

## Non-Goals (Out of Scope)
- 不修改图片和表格的章节分配逻辑（这部分逻辑已经正确）
- 不修改完整Markdown输出的逻辑
- 不修改其他功能模块

## Background & Context
- 当前按章节生成Markdown时，`_process_chapter_pages`方法按顺序添加所有文本块，然后添加所有图像，最后添加所有表格
- 完整Markdown输出的逻辑（`_process_pages`和`_process_page_elements`方法）会根据元素在页面中的实际位置来排序和插入
- 这种差异导致了章节Markdown中图片和表格位置不正确的问题

## Functional Requirements
- **FR-1**: 修复`_process_chapter_pages`方法，使其能够根据元素在页面中的实际位置来排序和插入文本块、图像和表格
- **FR-2**: 确保图片和表格被正确分配到它们所属的章节
- **FR-3**: 保持与完整Markdown输出逻辑的一致性

## Non-Functional Requirements
- **NFR-1**: 代码修改应保持简洁明了，易于理解和维护
- **NFR-2**: 修改后的代码应与现有代码风格保持一致
- **NFR-3**: 修改不应影响其他功能模块的正常运行

## Constraints
- **Technical**: 必须使用现有的代码结构和方法，不得引入新的依赖
- **Dependencies**: 依赖于现有的文本块、图像和表格数据结构

## Assumptions
- 文本块、图像和表格已经正确分配到了它们所属的章节
- 每个元素都有正确的位置信息（bbox）
- 原始文本块已经按垂直位置排序

## Acceptance Criteria

### AC-1: 图片和表格正确分配到所在章节
- **Given**: 一个包含多个章节的PDF文档，其中第三章包含图片
- **When**: 使用按章节生成Markdown功能
- **Then**: 第三章的图片应该出现在第三章的Markdown文件中，而不是第四章的Markdown文件中
- **Verification**: `programmatic`

### AC-2: 图片和表格位置正确
- **Given**: 一个包含文本块、图像和表格的页面
- **When**: 使用按章节生成Markdown功能
- **Then**: 图像和表格应该出现在Markdown文件中与它们在原始页面中相对应的文本块附近
- **Verification**: `human-judgment`

### AC-3: 与完整Markdown输出逻辑一致
- **Given**: 同一个PDF文档
- **When**: 分别使用完整Markdown输出和按章节生成Markdown功能
- **Then**: 两种方式生成的Markdown中，图片和表格的相对位置应该一致
- **Verification**: `human-judgment`

## Open Questions
- [ ] 如何处理跨章节页面的图片和表格？
- [ ] 是否需要修改图像和表格的章节分配逻辑？