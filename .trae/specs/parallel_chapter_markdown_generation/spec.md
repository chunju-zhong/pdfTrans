# PDF翻译工具 - 按章节并行生成Markdown功能优化

## Overview

* **Summary**: 优化当前按章节生成Markdown的实现，将顺序调用大模型生成改为多线程并行生成，提高生成速度。

* **Purpose**: 解决当前按章节生成Markdown时速度较慢的问题，通过并行处理提高整体翻译流程的效率。

* **Target Users**: 使用PDF翻译工具的用户，特别是处理长文档的用户。

## Goals

* 实现按章节并行生成Markdown文件，提高生成速度

* 保持章节内容的完整性和准确性

* 确保线程安全，避免文件写入冲突

* 保持与现有代码的兼容性

## Non-Goals (Out of Scope)

* 改变Markdown文件的生成内容和格式

* 修改章节内容的组织方式

* 优化其他翻译流程步骤

## Background & Context

* 当前实现中，按章节生成Markdown文件是顺序执行的，每个章节需要等待前一个章节处理完成后才能开始

* 每个章节的处理包括文本组织、调用大模型格式化和文件保存等步骤

* 大模型调用是一个耗时操作，顺序执行会导致整体生成时间较长

* 项目中已经在其他部分（如翻译文本块）使用了线程池进行并行处理

## Functional Requirements

* **FR-1**: 实现按章节并行生成Markdown文件的功能

* **FR-2**: 确保所有章节都能正确生成，没有内容丢失

* **FR-3**: 保持章节索引文件的正确生成

* **FR-4**: 确保线程安全，避免文件写入冲突

## Non-Functional Requirements

* **NFR-1**: 提高生成速度，减少用户等待时间

* **NFR-2**: 保持代码的可维护性和可读性

* **NFR-3**: 确保与现有代码的兼容性

## Constraints

* **Technical**: 使用Python的ThreadPoolExecutor进行并行处理

* **Dependencies**: 依赖于现有的Markdown生成逻辑和大模型API调用

## Assumptions

* 大模型API能够处理并发请求

* 系统资源（CPU、内存、网络）足够支持并行处理

## Acceptance Criteria

### AC-1: 并行生成功能实现

* **Given**: 一个包含多个章节的PDF文档

* **When**: 执行按章节生成Markdown操作

* **Then**: 多个章节的Markdown文件同时开始生成

* **Verification**: `programmatic`

### AC-2: 生成速度提升

* **Given**: 一个包含多个章节的PDF文档

* **When**: 比较优化前后的生成时间

* **Then**: 优化后的生成时间明显缩短（至少30%）

* **Verification**: `programmatic`

### AC-3: 内容完整性

* **Given**: 一个包含多个章节的PDF文档

* **When**: 并行生成Markdown文件

* **Then**: 所有章节的内容都能正确生成，没有内容丢失或重复

* **Verification**: `human-judgment`

### AC-4: 线程安全

* **Given**: 一个包含多个章节的PDF文档

* **When**: 并行生成Markdown文件

* **Then**: 没有文件写入冲突或其他线程安全问题

* **Verification**: `programmatic`

## Open Questions
- [x] 并行处理的最大线程数应该设置为多少？
  - 建议设置为配置中的 MAX_WORKERS 值，与其他并行处理保持一致
  - 默认为 4，可根据系统资源和API限制进行调整
- [x] 如何处理并行生成过程中的错误？
  - 每个章节的生成任务应该包含错误捕获
  - 一个章节的错误不会影响其他章节的生成
  - 错误信息应该被记录到日志中
  - 生成失败的章节应该在最终结果中被标记
  - 错误信息应该被上报到前端，便于用户了解生成状态
  - 对生成失败的章节应该进行重试，最多重试3次

