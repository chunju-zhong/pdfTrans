# PDF翻译工具 - 章节信息复制修复

## Overview
- **Summary**: 修复翻译过程中章节信息丢失的问题，确保翻译后的文本块包含完整的章节信息
- **Purpose**: 解决章节Markdown文件中缺少翻译文本的问题，确保翻译后的文本能够正确映射到对应的章节
- **Target Users**: PDF翻译工具的开发人员和维护人员

## Goals
- 修复合并块处理时章节信息丢失的问题
- 实现完整的TextBlock属性复制，避免未来添加新属性时再次出现类似问题
- 确保翻译后的文本块能够正确映射到对应的章节

## Non-Goals (Out of Scope)
- 修改TextBlock类的基本结构
- 改变章节识别和映射的核心逻辑
- 优化翻译API调用方式

## Background & Context
- 当前实现中，翻译后的TextBlock对象只复制了部分属性，导致章节信息丢失
- 章节信息包括chapter_id、chapter_title、chapter_level和chapter_number
- 丢失章节信息的文本块无法被markdown生成器正确映射到章节

## Functional Requirements
- **FR-1**: 翻译后的TextBlock对象应包含完整的章节信息
- **FR-2**: 实现TextBlock属性的完整复制，包括未来可能添加的新属性
- **FR-3**: 确保翻译后的文本块能够正确映射到对应的章节

## Non-Functional Requirements
- **NFR-1**: 代码修改应保持向后兼容
- **NFR-2**: 实现方式应简洁高效，不增加系统复杂度
- **NFR-3**: 修复应覆盖所有创建翻译TextBlock的场景

## Constraints
- **Technical**: 需要保持与现有TextBlock类结构的兼容性
- **Dependencies**: 依赖于TextBlock类的当前实现

## Assumptions
- TextBlock类的属性结构是稳定的
- 章节信息在PDF提取阶段正确关联到文本块

## Acceptance Criteria

### AC-1: 翻译后的TextBlock包含完整章节信息
- **Given**: 原始TextBlock包含章节信息
- **When**: 创建翻译后的TextBlock对象
- **Then**: 翻译后的TextBlock应包含与原始TextBlock相同的章节信息
- **Verification**: `programmatic`
- **Notes**: 包括chapter_id、chapter_title、chapter_level和chapter_number

### AC-2: 新属性自动复制
- **Given**: TextBlock类添加了新属性
- **When**: 创建翻译后的TextBlock对象
- **Then**: 新属性应自动从原始TextBlock复制到翻译后的TextBlock
- **Verification**: `human-judgment`
- **Notes**: 无需修改复制逻辑即可支持新属性

### AC-3: 章节Markdown文件包含翻译文本
- **Given**: 处理包含章节的PDF文档
- **When**: 生成章节Markdown文件
- **Then**: 章节文件应包含翻译后的文本内容
- **Verification**: `human-judgment`
- **Notes**: 不再出现"文本块未找到对应章节"的警告

## Open Questions
- [ ] 最佳的TextBlock复制方式是什么？
- [ ] 是否需要在TextBlock类中添加复制方法？