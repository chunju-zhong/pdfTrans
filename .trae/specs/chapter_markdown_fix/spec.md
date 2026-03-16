# 章节Markdown生成问题修复 - 产品需求文档

## Overview
- **Summary**: 修复PDF翻译工具中章节Markdown生成功能的问题，确保能够正确识别和生成所有章节的Markdown文件，包括嵌套章节。
- **Purpose**: 解决章节Markdown生成不完整的问题，确保每个章节都能生成包含完整内容的Markdown文件。
- **Target Users**: 使用PDF翻译工具的用户，特别是需要按章节生成Markdown文件的用户。

## Goals
- 修复章节识别和映射逻辑，确保所有章节都能被正确识别和关联
- 修复章节内容组织逻辑，确保每个章节都能包含完整的文本、图像和表格内容
- 确保嵌套章节能够正确生成对应的Markdown文件
- 验证修复效果，确保所有章节都能正确生成

## Non-Goals (Out of Scope)
- 不修改PDF提取逻辑
- 不修改翻译逻辑
- 不修改其他输出格式（如PDF、Word）的生成逻辑

## Background & Context
- 之前已经修复了章节映射逻辑，确保所有页码都能正确关联到对应的章节
- 但仍然存在章节内容组织的问题，导致只有部分章节能够生成，且内容不完整
- 日志显示检测到9个章节，但最终只生成了1个章节文件

## Functional Requirements
- **FR-1**: 正确识别PDF中的所有章节，包括嵌套章节
- **FR-2**: 为每个章节生成对应的Markdown文件，文件名包含章节编号和标题
- **FR-3**: 每个章节文件包含该章节的完整文本、图像和表格内容
- **FR-4**: 生成章节索引文件，包含所有章节的链接

## Non-Functional Requirements
- **NFR-1**: 章节Markdown生成过程应该有详细的日志记录，便于调试和问题追踪
- **NFR-2**: 代码应该清晰可维护，避免复杂的逻辑
- **NFR-3**: 修复应该不影响其他功能的正常运行

## Constraints
- **Technical**: 保持与现有代码结构的兼容性
- **Dependencies**: 依赖PyMuPDF进行PDF书签提取

## Assumptions
- PDF文档包含有效的书签结构
- 书签结构能够正确反映章节层次

## Acceptance Criteria

### AC-1: 所有章节都能被正确识别
- **Given**: PDF文档包含多个章节和嵌套章节
- **When**: 运行章节Markdown生成功能
- **Then**: 系统应该检测到所有章节，包括嵌套章节
- **Verification**: `programmatic`
- **Notes**: 日志应该显示检测到的章节数量与实际章节数量一致

### AC-2: 每个章节都能生成对应的Markdown文件
- **Given**: PDF文档包含多个章节
- **When**: 运行章节Markdown生成功能
- **Then**: 系统应该为每个章节生成对应的Markdown文件
- **Verification**: `human-judgment`
- **Notes**: 生成的文件数量应该与章节数量一致

### AC-3: 章节文件包含完整的内容
- **Given**: PDF文档的章节包含文本、图像和表格
- **When**: 运行章节Markdown生成功能
- **Then**: 生成的章节Markdown文件应该包含该章节的完整文本、图像和表格内容
- **Verification**: `human-judgment`
- **Notes**: 章节文件不应为空，应包含对应章节的所有内容

### AC-4: 嵌套章节能够正确生成
- **Given**: PDF文档包含嵌套章节
- **When**: 运行章节Markdown生成功能
- **Then**: 系统应该为每个嵌套章节生成对应的Markdown文件，文件名包含正确的层级编号
- **Verification**: `human-judgment`
- **Notes**: 嵌套章节的文件名应该使用正确的编号格式，如1.1、1.1.1等

## Open Questions
- [ ] 为什么检测到9个章节但只生成了1个章节文件？
- [ ] 章节映射逻辑是否正确处理了嵌套章节？
- [ ] 章节内容组织逻辑是否正确处理了不同层级的章节？