# PDF翻译工具 - 多线程并发术语提取功能 - 产品需求文档

## Overview

* **Summary**: 实现按页多线程并发调用术语提取功能，提高大PDF文件的术语提取速度。

* **Purpose**: 解决大PDF文件术语提取速度慢的问题，通过并行处理提高效率。

* **Target Users**: PDF翻译工具的开发者和终端用户。

## Goals
- 实现按页多线程并发处理术语提取
- 提高大PDF文件的术语提取速度
- 保持与现有术语提取功能相同的输出格式
- 确保线程安全和结果正确性
- 对提取的术语进行排序并去重
- 在按页处理时更新进度条信息

## Non-Goals (Out of Scope)

* 改变现有的术语提取算法

* 修改其他服务的功能

* 引入新的依赖库

## Background & Context

* 当前的术语提取服务是单线程处理，对大PDF文件提取速度较慢

* 术语提取是CPU密集型任务，适合并行处理

* 现有代码结构支持按页提取文本，为并行处理提供了基础

## Functional Requirements
- **FR-1**: 按页提取PDF文本，而不是一次性提取所有文本
- **FR-2**: 使用线程池并发处理多个页面的术语提取
- **FR-3**: 合并来自所有页面的术语提取结果，去除重复术语并排序
- **FR-4**: 保持与现有术语提取功能相同的输出格式
- **FR-5**: 在按页处理时更新进度条信息

## Non-Functional Requirements

* **NFR-1**: 对于大PDF文件，术语提取速度应比单线程版本显著提高

* **NFR-2**: 确保线程安全，避免并发访问导致的问题

* **NFR-3**: 保持代码的可读性和可维护性

## Constraints

* **Technical**: 使用Python标准库的concurrent.futures模块实现线程池

* **Technical**: 保持与现有代码结构的兼容性

* **Dependencies**: 依赖现有的PdfExtractor和GlossaryExtractor类

## Assumptions

* 术语提取是CPU密集型任务，适合并行处理

* 不同页面的术语提取是相互独立的

* 线程池大小应根据系统CPU核心数动态调整

## Acceptance Criteria

### AC-1: 多线程并发处理功能

* **Given**: 上传一个包含多个页面的PDF文件

* **When**: 点击"提取术语"按钮

* **Then**: 系统应使用多线程并发处理各页面的术语提取

* **Verification**: `programmatic`

### AC-2: 性能 improvement

* **Given**: 上传一个包含50页以上的PDF文件

* **When**: 比较单线程和多线程版本的术语提取时间

* **Then**: 多线程版本的提取时间应显著短于单线程版本

* **Verification**: `programmatic`

### AC-3: 结果正确性
- **Given**: 上传一个PDF文件
- **When**: 使用多线程版本提取术语
- **Then**: 提取的术语表应与单线程版本相同，格式正确，并且术语已排序
- **Verification**: `programmatic`

### AC-5: 进度条更新
- **Given**: 上传一个包含多个页面的PDF文件
- **When**: 点击"提取术语"按钮
- **Then**: 进度条应显示按页处理的进度信息
- **Verification**: `human-judgment`

### AC-4: 线程安全

* **Given**: 同时处理多个PDF文件的术语提取

* **When**: 系统并发执行多个术语提取任务

* **Then**: 系统应正常运行，无线程冲突或数据损坏

* **Verification**: `human-judgment`

## Open Questions

* [ ] 线程池大小的最佳配置是多少？

* [ ] 如何处理术语重复的情况？

* [ ] 是否需要为不同大小的PDF文件调整线程池大小？

