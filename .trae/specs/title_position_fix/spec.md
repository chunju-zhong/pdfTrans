# PDF章节标题位置识别修复 - Product Requirement Document

## Overview
- **Summary**: 修复PDF章节标题位置识别中的误匹配问题，通过改进文本匹配算法提高章节位置识别的准确性，支持处理跨多个连续文本块的标题，确保文本块能够正确关联到相应的章节。
- **Purpose**: 解决当前章节标题识别算法中因使用前15个字符模糊匹配导致的文本块误识别问题，以及标题可能跨多个连续文本块的问题，特别是像"Introduction to Agents and Agent architectures"被错误识别为"Agents and Agent"章节标题的场景。
- **Target Users**: PDF翻译工具的所有用户，特别是处理包含复杂章节标题的技术文档的用户。

## Goals
- 修复章节标题位置识别中的误匹配问题
- 支持识别跨多个连续文本块的标题
- 提高章节位置识别的准确率
- 确保文本块、表格、图像能够正确关联到相应章节
- 保持原有的功能完整性和性能

## Non-Goals (Out of Scope)
- 不改变PDF书签提取的整体架构
- 不修改文本块、表格、图像关联到章节的核心逻辑
- 不添加新的翻译API或功能
- 不考虑字体样式分析（本阶段不涉及）
- 不重构整个章节识别模块

## Background & Context
当前PDF翻译工具使用PyMuPDF提取PDF书签信息，并通过`_find_title_position`方法在页面中查找章节标题的具体位置。该方法存在两个主要问题：

1. 使用标题的前15个字符进行模糊匹配，导致当一个文本块包含另一个章节标题的子字符串时，会被错误地识别为该章节的标题文本块。例如，章节标题"Agents and Agent"的前15个字符是"Agents and Agent"，而文本块"Introduction to Agents and Agent architectures"中也包含了这个子字符串，导致被错误地匹配。

2. 标题文本可能跨多个连续的文本块，当前算法只检查单个文本块，无法处理这种情况。

## Functional Requirements
- **FR-1**: 改进`_find_title_position`方法，使用更精确的文本匹配算法识别章节标题文本块
- **FR-2**: 优先寻找与标题完全匹配的单个文本块
- **FR-3**: 支持识别跨多个连续文本块的标题
- **FR-4**: 然后寻找高度相似的文本块（使用文本相似度算法）
- **FR-5**: 在多个候选文本块中选择最可能是标题的那个

## Non-Functional Requirements
- **NFR-1**: 修复后的算法应该与原算法保持相当或更好的性能
- **NFR-2**: 修复应该向后兼容，不破坏现有功能
- **NFR-3**: 代码修改应该遵循项目的代码风格和规范

## Constraints
- **Technical**: 必须使用Python 3.9+，PyMuPDF 1.23+
- **Business**: 必须在不影响现有用户体验的前提下进行修复
- **Dependencies**: 仅依赖项目已有的库，不引入新的第三方库

## Assumptions
- 大多数情况下，页面中会存在与标题完全匹配的文本块
- 标题文本可能作为一个完整的文本块存在，也可能跨多个连续的文本块
- 连续文本块在垂直位置上是相邻的
- 使用文本相似度算法可以有效区分标题和包含子字符串的文本

## Acceptance Criteria

### AC-1: 精确匹配优先（单个文本块）
- **Given**: 页面中有一个文本块与章节标题完全匹配
- **When**: 调用`_find_title_position`方法查找该章节标题的位置
- **Then**: 应该返回完全匹配的文本块的位置
- **Verification**: `programmatic`
- **Notes**: 完全匹配的优先级最高

### AC-2: 支持跨多个连续文本块的标题
- **Given**: 章节标题跨多个连续的文本块
- **When**: 调用`_find_title_position`方法查找该章节标题的位置
- **Then**: 应该能够识别这些连续文本块并返回第一个文本块的位置
- **Verification**: `programmatic`

### AC-3: 避免子字符串误匹配
- **Given**: 章节标题是"Agents and Agent"，页面中有文本块"Introduction to Agents and Agent architectures"
- **When**: 调用`_find_title_position`方法查找"Agents and Agent"章节的位置
- **Then**: 不应该返回"Introduction to Agents and Agent architectures"文本块的位置
- **Verification**: `programmatic`

### AC-4: 向后兼容
- **Given**: 修复后的代码
- **When**: 运行原有的测试用例
- **Then**: 所有测试用例都应该通过
- **Verification**: `programmatic`

### AC-5: 代码质量
- **Given**: 修复后的代码
- **When**: 进行代码审查
- **Then**: 代码应该符合项目的代码风格和规范
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要添加配置项来调整匹配算法的参数？
- [ ] 是否需要为特定PDF格式添加特殊处理逻辑？
- [ ] 跨文本块的标题最多允许跨越多少个文本块？
