# Markdown生成器图表位置修复 - 需求文档

## Overview
- **Summary**: 修复按章节生成Markdown时丢失图表位置逻辑的问题，确保图表能够按照原始文档中的位置关系正确插入到章节内容中。
- **Purpose**: 保证按章节生成的Markdown文档与原始文档的布局一致，提高翻译结果的可读性和准确性。
- **Target Users**: 需要翻译和管理PDF文档的用户，特别是处理包含图表的长文档的用户。

## Goals
- 修复按章节生成Markdown时图表位置丢失的问题
- 重用现有的`_process_page_elements`逻辑来处理图表位置
- 确保图表在章节Markdown中正确插入到文本块的适当位置
- 保持与现有功能的兼容性

## Non-Goals (Out of Scope)
- 不修改现有的PDF提取和翻译核心逻辑
- 不改变现有的API调用方式
- 不影响其他输出格式（PDF、Word）的生成

## Background & Context
- 当前系统已经实现了完整的PDF提取、翻译和Markdown生成功能
- 现有的`_process_page_elements`方法能够根据原始文档中的位置关系正确插入图表
- 但在按章节生成Markdown时，这个逻辑没有被重用，导致图表只能简单地添加到章节末尾

## Functional Requirements
- **FR-1**: 按章节组织内容时，正确处理图表的位置关系
- **FR-2**: 重用现有的`_process_page_elements`逻辑来处理图表位置
- **FR-3**: 确保图表在章节Markdown中按照原始文档的布局插入

## Non-Functional Requirements
- **NFR-1**: 性能要求 - 图表位置处理不应显著增加生成时间
- **NFR-2**: 兼容性 - 保持与现有系统的兼容性
- **NFR-3**: 可维护性 - 代码结构清晰，易于维护和扩展

## Constraints
- **Technical**: 基于现有的Markdown生成器架构
- **Dependencies**: 依赖现有的`_process_page_elements`方法

## Assumptions
- PDF文档包含图表元素（图像或表格）
- 图表元素有明确的位置信息（bbox）
- 文本块和图表元素已经按页码组织

## Acceptance Criteria

### AC-1: 图表位置正确
- **Given**: 上传包含图表的PDF文档
- **When**: 执行按章节生成Markdown
- **Then**: 图表在章节Markdown中正确插入到文本块的适当位置
- **Verification**: `human-judgment`

### AC-2: 重用现有逻辑
- **Given**: 系统实现了图表位置修复
- **When**: 查看代码实现
- **Then**: 代码重用了现有的`_process_page_elements`逻辑
- **Verification**: `human-judgment`

### AC-3: 与现有功能兼容
- **Given**: 系统实现了图表位置修复
- **When**: 运行所有测试用例
- **Then**: 所有测试用例通过
- **Verification**: `programmatic`

## Open Questions
- [ ] 如何处理跨章节的图表？
- [ ] 如何确保章节内的文本块和图表正确排序？