# 图片插入位置错误问题分析 - 产品需求文档

## Overview
- **Summary**: 分析Word和Markdown生成器中图片插入位置错误的根本原因，特别是12页图片应该在"initial Mission is achieved"之后、"Figure 1: Agentic AI problem-solving process"之前的问题。
- **Purpose**: 找出图片位置计算的缺陷，为后续修复提供明确的方向。
- **Target Users**: 开发团队，特别是负责PDF翻译工具中文档生成功能的开发者。

## Goals
- 分析图片位置计算的逻辑缺陷
- 确定导致12页图片位置错误的根本原因
- 提供修复建议和验证方案
- 确保图片在生成的文档中位于正确的文本位置

## Non-Goals (Out of Scope)
- 实际修改代码
- 测试其他页面的图片位置
- 优化文档生成性能

## Background & Context
- 项目使用PyMuPDF进行PDF文本提取
- 生成器使用合并块（MergedBlock）来组织文本
- 图片位置基于原始文本块的坐标计算
- 当前逻辑在处理合并块时可能存在位置计算不准确的问题

## Functional Requirements
- **FR-1**: 图片应该根据其在原始PDF中的位置，插入到生成文档的正确文本位置
- **FR-2**: 图片插入位置应该考虑文本的语义结构，特别是标题和段落的关系
- **FR-3**: 生成器应该能够处理合并块内的图片位置计算

## Non-Functional Requirements
- **NFR-1**: 位置计算逻辑应该准确反映原始PDF的布局
- **NFR-2**: 计算过程应该清晰可追踪，便于调试
- **NFR-3**: 修复方案应该对现有代码的影响最小

## Constraints
- **Technical**: 基于现有的合并块结构和位置计算逻辑
- **Dependencies**: 依赖于PyMuPDF提取的文本块和图片位置信息

## Assumptions
- 原始PDF中的图片位置信息是准确的
- 文本块的合并逻辑是合理的
- 图片位置计算应该基于文本的垂直位置

## Acceptance Criteria

### AC-1: 图片位置计算准确性
- **Given**: 原始PDF中图片位于特定文本之间
- **When**: 生成Word或Markdown文档时
- **Then**: 图片应该插入到对应文本之间的正确位置
- **Verification**: `human-judgment`

### AC-2: 合并块处理
- **Given**: 图片周围的文本被合并为一个大的合并块
- **When**: 计算图片插入位置时
- **Then**: 应该能够在合并块内找到准确的插入点
- **Verification**: `programmatic`

### AC-3: 12页图片位置
- **Given**: 12页图片位于"initial Mission is achieved"之后、"Figure 1: Agentic AI problem-solving process"之前
- **When**: 生成文档时
- **Then**: 图片应该插入到这两个文本之间
- **Verification**: `human-judgment`

## Open Questions
- [ ] 合并块的具体合并逻辑是什么？
- [ ] 原始文本块的坐标信息是否完整？
- [ ] 图片位置计算是否考虑了文本的语义结构？