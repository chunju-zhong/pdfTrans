# PDF翻译工具 - 章节Markdown生成优化规范

## Overview
- **Summary**: 优化PDF翻译工具的章节Markdown生成功能，确保不同章节的文本块不进行语义合并，并使用合并块数据生成章节Markdown文件。
- **Purpose**: 提高章节Markdown生成的准确性和一致性，确保章节边界清晰，避免跨章节的语义合并。
- **Target Users**: PDF翻译工具的用户，特别是需要按章节生成Markdown文档的用户。

## Goals
- 确保不同章节的文本块不进行语义合并
- 按章节生成Markdown时使用合并块数据，提高翻译质量和一致性
- 保持章节边界清晰，确保每个章节的内容独立完整

## Non-Goals (Out of Scope)
- 不修改PDF提取逻辑
- 不修改翻译API调用逻辑
- 不修改其他输出格式的生成逻辑（如PDF和Word）

## Background & Context
当前的实现中，语义合并逻辑没有考虑章节信息，可能会将不同章节的文本块合并在一起，导致章节边界模糊。同时，按章节生成Markdown时使用的是原始文本块，而不是合并后的语义块，可能会影响翻译质量和一致性。

## Functional Requirements
- **FR-1**: 语义合并逻辑应检查章节信息，确保不同章节的文本块不被合并
- **FR-2**: 按章节生成Markdown时应使用合并块数据，而不是原始文本块
- **FR-3**: 合并块数据应保留原始块的章节信息，以便按章节拆分

## Non-Functional Requirements
- **NFR-1**: 优化后的语义合并逻辑不应显著增加处理时间
- **NFR-2**: 按章节生成Markdown的性能应保持稳定
- **NFR-3**: 代码修改应保持与现有代码风格一致

## Constraints
- **Technical**: 代码修改应兼容现有的数据模型和API
- **Dependencies**: 依赖现有的文本块和章节数据结构

## Assumptions
- 文本块和合并块都包含章节信息（chapter_id、chapter_title等）
- 章节信息在PDF提取阶段已经正确设置

## Acceptance Criteria

### AC-1: 不同章节的块不进行语义合并
- **Given**: 输入包含多个章节的PDF文档
- **When**: 执行语义合并操作
- **Then**: 不同章节的文本块不会被合并到同一个语义块中
- **Verification**: `programmatic`

### AC-2: 按章节生成Markdown使用合并块数据
- **Given**: 输入包含章节信息的翻译结果
- **When**: 生成章节Markdown文件
- **Then**: 使用合并块数据生成，而不是原始文本块
- **Verification**: `programmatic`

### AC-3: 章节边界清晰
- **Given**: 输入包含多个章节的PDF文档
- **When**: 生成章节Markdown文件
- **Then**: 每个章节的内容独立完整，章节边界清晰
- **Verification**: `human-judgment`

## Open Questions
- [ ] 如何处理跨页的章节边界？
- [ ] 如何确保合并块的章节信息与原始块一致？