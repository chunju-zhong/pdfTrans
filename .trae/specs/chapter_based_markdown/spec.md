# PDF翻译工具 - 按章节生成Markdown功能需求文档

## Overview
- **Summary**: 实现按PDF章节提取翻译并生成不同Markdown文件的功能，使用户在全选翻译所有页面时能够获得按章节组织的Markdown输出。
- **Purpose**: 提高翻译结果的可读性和组织性，便于用户按章节查看和管理翻译内容。
- **Target Users**: 需要翻译和管理PDF文档的用户，特别是处理长文档的用户。

## Goals
- 实现PDF章节识别和提取功能
- 按章节组织翻译内容
- 为每个章节生成单独的Markdown文件
- 保持现有功能的完整性和兼容性

## Non-Goals (Out of Scope)
- 不修改现有的PDF提取和翻译核心逻辑
- 不改变现有的API调用方式
- 不影响其他输出格式（PDF、Word）的生成

## Background & Context
- 当前系统已经实现了完整的PDF提取、翻译和Markdown生成功能
- 现有的Markdown生成器能够生成单个Markdown文件，但不能按章节拆分
- 用户需要更结构化的翻译结果，特别是对于长文档

## Functional Requirements
- **FR-1**: 使用PDF书签(bookmark)识别章节结构
- **FR-2**: 按章节组织翻译后的内容
- **FR-3**: 为每个章节生成单独的Markdown文件
- **FR-4**: 生成章节索引文件，方便用户导航
- **FR-5**: 对没有明确章节结构的PDF文档，提示不支持按章节生成Markdown

## Non-Functional Requirements
- **NFR-1**: 性能要求 - 章节识别和处理不应显著增加翻译时间
- **NFR-2**: 兼容性 - 保持与现有系统的兼容性
- **NFR-3**: 可维护性 - 代码结构清晰，易于维护和扩展

## Constraints
- **Technical**: 基于现有的PDF提取和Markdown生成架构
- **Dependencies**: 依赖PyMuPDF进行PDF解析
- **Design**: 章节嵌套最多支持3层

## Assumptions
- PDF文档具有明确的章节结构（通过书签识别）
- PDF文档包含有效的书签信息

## Acceptance Criteria

### AC-1: 章节识别
- **Given**: 上传包含章节结构的PDF文档
- **When**: 执行全选翻译
- **Then**: 系统能够正确识别文档中的章节结构
- **Verification**: `programmatic`

### AC-2: 按章节翻译
- **Given**: 系统已识别章节结构
- **When**: 执行翻译流程
- **Then**: 翻译内容按章节组织
- **Verification**: `programmatic`

### AC-3: 多Markdown文件生成
- **Given**: 翻译完成后选择Markdown输出格式
- **When**: 生成输出文件
- **Then**: 为每个章节生成单独的Markdown文件
- **Verification**: `programmatic`

### AC-4: 章节索引文件
- **Given**: 多Markdown文件生成完成
- **When**: 查看输出结果
- **Then**: 生成包含所有章节链接的索引文件
- **Verification**: `human-judgment`

## Nested Chapter Handling
- **Level 1 Chapters**: 生成Markdown文件，文件名为 "1. 章节标题.md" 格式
- **Level 2 Chapters**: 生成Markdown文件，文件名为 "1.1. 章节标题.md" 格式
- **Level 3 Chapters**: 生成Markdown文件，文件名为 "1.1.1. 章节标题.md" 格式
- **Levels Beyond 3**: 不再进一步拆分，将内容合并到最近的Level 3章节中

## Open Questions
- [ ] 无