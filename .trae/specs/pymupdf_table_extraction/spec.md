# PyMuPDF表格提取功能 - 产品需求文档

## Overview
- **Summary**: 实现基于PyMuPDF的表格提取功能，与现有的基于Camelot的表格提取功能保持相同的接口和返回值格式。
- **Purpose**: 提供一种不依赖Camelot库的表格提取方案，提高系统的兼容性和可靠性。
- **Target Users**: 开发人员，用于在PDF翻译工具中提取表格内容。

## Goals
- 实现使用PyMuPDF提取PDF表格的功能
- 保持与现有`extract_tables_by_camelot`函数相同的参数和返回值格式
- 确保提取的表格数据结构与现有实现兼容
- 提供可靠的表格边界框提取和处理

## Non-Goals (Out of Scope)
- 不修改现有的Camelot-based表格提取功能
- 不改变表格数据的处理逻辑
- 不添加新的参数或返回值

## Background & Context
- 当前系统使用Camelot库进行表格提取，但Camelot依赖较多且可能在某些环境下安装困难
- PyMuPDF是系统已有的依赖，用于PDF文本提取，使用它来提取表格可以减少依赖
- 现有的`extract_tables_by_camelot`函数定义了标准的表格提取接口，新实现需要保持兼容

## Functional Requirements
- **FR-1**: 实现`extract_tables_by_pymupdf`函数，接受与`extract_tables_by_camelot`相同的参数
- **FR-2**: 返回与`extract_tables_by_camelot`相同格式的结果（表格列表和按页码组织的边界框字典）
- **FR-3**: 支持指定页码范围的表格提取
- **FR-4**: 处理表格边界框的提取和坐标系转换
- **FR-5**: 构建与现有实现兼容的表格数据结构

## Non-Functional Requirements
- **NFR-1**: 提取性能不低于现有Camelot实现
- **NFR-2**: 代码质量符合项目的代码风格规范
- **NFR-3**: 提供适当的日志记录

## Constraints
- **Technical**: 仅使用PyMuPDF库，不依赖Camelot
- **Dependencies**: 依赖PyMuPDF库进行PDF处理

## Assumptions
- 系统已安装PyMuPDF库
- 现有的表格数据结构和处理逻辑保持不变

## Acceptance Criteria

### AC-1: 函数接口一致性
- **Given**: 调用`extract_tables_by_pymupdf`函数
- **When**: 传入与`extract_tables_by_camelot`相同的参数
- **Then**: 函数能够正常执行并返回相同格式的结果
- **Verification**: `programmatic`

### AC-2: 表格提取功能
- **Given**: 提供包含表格的PDF文件
- **When**: 调用`extract_tables_by_pymupdf`函数
- **Then**: 函数能够提取PDF中的表格并返回正确的表格数据
- **Verification**: `programmatic`

### AC-3: 页码范围支持
- **Given**: 提供包含多个表格的PDF文件
- **When**: 调用`extract_tables_by_pymupdf`函数并指定页码范围
- **Then**: 函数只提取指定页码范围内的表格
- **Verification**: `programmatic`

### AC-4: 边界框处理
- **Given**: 提供包含表格的PDF文件
- **When**: 调用`extract_tables_by_pymupdf`函数
- **Then**: 函数能够正确提取表格的边界框并转换为PyMuPDF坐标系
- **Verification**: `programmatic`

### AC-5: 兼容性
- **Given**: 现有的代码使用`extract_tables_by_camelot`函数
- **When**: 将调用替换为`extract_tables_by_pymupdf`
- **Then**: 系统能够正常运行，无需修改其他代码
- **Verification**: `programmatic`

## Open Questions
- [ ] PyMuPDF的表格提取准确性与Camelot相比如何？
- [ ] 是否需要处理特殊表格格式（如合并单元格）？