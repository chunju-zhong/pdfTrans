# PDF翻译工具 - 前端UI增加显示翻译总耗时功能

## Overview
- **Summary**: 为PDF翻译工具的前端UI增加显示翻译总耗时的功能，让用户能够直观了解翻译任务的处理时间。
- **Purpose**: 提供翻译任务的时间消耗信息，帮助用户评估翻译效率和服务性能。
- **Target Users**: 使用PDF翻译工具的所有用户。

## Goals
- 在翻译完成后，在前端UI中显示翻译任务的总耗时
- 确保耗时计算准确，包括整个翻译流程的时间
- 提供友好的时间显示格式，易于用户理解

## Non-Goals (Out of Scope)
- 不修改翻译算法或性能优化
- 不增加额外的后端存储或数据库需求
- 不改变现有的翻译流程和功能

## Background & Context
- 目前PDF翻译工具已经实现了完整的翻译流程，包括PDF上传、文本提取、翻译和文件生成
- 前端UI已经有完整的进度显示和结果展示功能
- 后端使用Task对象管理翻译任务，包含状态、进度、结果等信息

## Functional Requirements
- **FR-1**: 后端Task模型增加开始时间和结束时间属性
- **FR-2**: 翻译服务在任务开始和结束时记录时间
- **FR-3**: get_progress API返回翻译耗时信息
- **FR-4**: 前端UI在翻译完成后显示耗时信息

## Non-Functional Requirements
- **NFR-1**: 耗时计算准确，误差不超过1秒
- **NFR-2**: 前端显示格式友好，使用分:秒格式
- **NFR-3**: 不影响现有功能的性能和稳定性

## Constraints
- **Technical**: 基于现有Flask框架和前端JavaScript实现
- **Dependencies**: 仅使用Python标准库的time模块

## Assumptions
- 翻译任务的开始时间从任务创建时计算
- 翻译任务的结束时间从任务完成时计算
- 前端可以处理和显示时间格式

## Acceptance Criteria

### AC-1: 后端Task模型增加时间属性
- **Given**: 后端Task模型已存在
- **When**: 修改Task类，添加start_time和end_time属性
- **Then**: Task对象能够记录任务的开始和结束时间
- **Verification**: `programmatic`

### AC-2: 翻译服务记录时间
- **Given**: 翻译服务处理翻译任务
- **When**: 任务开始和结束时，记录时间到Task对象
- **Then**: Task对象的start_time和end_time属性被正确设置
- **Verification**: `programmatic`

### AC-3: API返回耗时信息
- **Given**: 前端调用get_progress API
- **When**: 任务完成时，API返回耗时信息
- **Then**: API响应中包含total_time字段，表示翻译总耗时（秒）
- **Verification**: `programmatic`

### AC-4: 前端显示耗时信息
- **Given**: 翻译任务完成
- **When**: 前端收到完成状态和耗时信息
- **Then**: 前端在结果区域显示翻译总耗时，格式为"翻译总耗时：X分X秒"
- **Verification**: `human-judgment`

## Open Questions
- [x] 是否需要在任务取消或失败时也计算耗时？ - 是的，任务取消或失败时也应该计算耗时
- [x] 是否需要在进度显示过程中实时更新耗时？ - 是的，应该在进度显示过程中实时更新耗时