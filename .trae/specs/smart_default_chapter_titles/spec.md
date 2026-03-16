# 智能默认章节命名功能 - 产品需求文档

## Overview

* **Summary**: 改进默认章节命名功能，使用页面的第一个文本块作为章节名，替代固定的标题列表（封面、目录、前言、引言），使章节名更加贴合实际内容

* **Purpose**: 解决固定默认章节标题不够灵活、与实际PDF内容不符的问题，提供更智能、更符合实际内容的章节命名

* **Target Users**: PDF翻译工具的所有用户

## Goals

* 使用页面的第一个文本块作为默认章节名

* 保持向后兼容（仍支持固定标题列表作为fallback）

* 提高章节命名的准确性和相关性

* 保持现有功能的完整性

## Non-Goals (Out of Scope)

* 修改章节关联逻辑

* 修改章节提取逻辑

* 修改Markdown生成逻辑

## Background & Context

* 当前实现使用固定标题列表：\["封面", "目录", "前言", "引言"]

* 从日志中可以看到，实际PDF内容可能与这些固定标题不符

* 使用页面第一个文本块作为章节名会更加符合实际内容

* 需要保持向后兼容性，以防页面没有文本块的情况

## Functional Requirements

* **FR-1**: 从PDF页面提取第一个文本块作为章节名

* **FR-2**: 如果页面没有文本块，使用固定标题列表作为fallback

* **FR-3**: 保持现有的默认章节配置参数作为fallback选项

* **FR-4**: 添加配置选项可以选择使用智能命名或固定命名

## Non-Functional Requirements

* **NFR-1**: 性能影响可忽略（不增加超过50ms的处理时间）

* **NFR-2**: 向后兼容，现有代码不需要修改

* **NFR-3**: 不影响现有的章节关联功能

## Constraints

* **Technical**: 必须在 `ChapterIdentifier` 类中实现

* **Business**: 必须保持API接口兼容性

* **Dependencies**: 需要访问PDF页面内容（可能需要修改接口设计）

## Assumptions

* 大多数PDF页面都有至少一个文本块

* 页面的第一个文本块通常能代表页面内容

* 如果没有文本块，使用固定标题是可接受的fallback

## Acceptance Criteria

### AC-1: 使用页面第一个文本块作为章节名

* **Given**: PDF页面有文本块

* **When**: 为该页面创建默认章节时

* **Then**: 章节名应为该页面的第一个文本块（截断到合适长度）

* **Verification**: `programmatic`

* **Notes**: 文本块长度超过20字符时截断

### AC-2: 无文本块时使用文件名和页号作为fallback

* **Given**: PDF页面没有文本块

* **When**: 为该页面创建默认章节时

* **Then**: 章节名应使用格式「{文件名}-第{页号}页」

* **Verification**: `programmatic`

### AC-3: 保持向后兼容

* **Given**: 现有代码使用固定标题列表

* **When**: 启用智能命名功能

* **Then**: 现有功能应继续正常工作

* **Verification**: `programmatic`

### AC-4: 可配置命名策略

* **Given**: 用户希望选择命名策略

* **When**: 初始化ChapterIdentifier时

* **Then**: 应支持配置使用智能命名或固定命名

* **Verification**: `programmatic`

### AC-5: 截断长文本块

* **Given**: 页面第一个文本块很长（超过20字符）

* **When**: 用作章节名时

* **Then**: 文本应被截断到20字符，并添加省略号

* **Verification**: `programmatic`

## Open Questions

* [ ] 如何访问PDF页面内容？当前设计中\_create\_default\_chapters方法没有PDF路径参数

* [ ] 文本块截断长度设为多少合适？（建议：20字符）

* [ ] 是否需要过滤页眉页脚等非正文文本块？

