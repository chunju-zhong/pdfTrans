# PDF翻译工具 - 按章节拆分Markdown功能开关

## Overview
- **Summary**: 为PDF翻译工具添加按章节拆分Markdown的功能开关，允许用户在前端UI选择是否按章节拆分生成Markdown文档
- **Purpose**: 提供更灵活的Markdown生成选项，满足用户对章节结构的不同需求
- **Target Users**: 使用PDF翻译工具生成Markdown文档的用户

## Goals
- 在前端UI添加按章节拆分Markdown的选择开关
- 后端根据用户选择执行相应的章节拆分逻辑
- 确保按章节拆分时正确处理章节相关的提取分析和生成功能

## Non-Goals (Out of Scope)
- 修改现有的Markdown生成核心逻辑
- 改变其他输出格式的生成方式
- 添加新的翻译API支持

## Background & Context
- 系统已有的Markdown生成功能支持章节信息处理
- 目前系统会根据是否存在章节信息自动决定是否按章节生成
- 需要添加用户可控的开关，让用户可以明确选择是否按章节拆分

## Functional Requirements
- **FR-1**: 前端UI添加按章节拆分Markdown的复选框
- **FR-2**: 后端接收并处理按章节拆分的参数
- **FR-3**: 当选择按章节拆分时，执行章节相关的提取分析和生成功能
- **FR-4**: 当不选择按章节拆分时，生成单一Markdown文件
- **FR-5**: 当不选择按章节拆分时，不执行章节相关的提取分析代码

## Non-Functional Requirements
- **NFR-1**: 保持UI界面的简洁性和易用性
- **NFR-2**: 确保功能开关不影响其他功能的正常运行
- **NFR-3**: 保持代码的可维护性和可测试性

## Constraints
- **Technical**: 基于现有的Flask框架和Markdown生成逻辑
- **Dependencies**: 依赖现有的章节提取和Markdown生成功能

## Assumptions
- 系统已经具备章节提取和按章节生成Markdown的能力
- 用户了解按章节拆分的含义和效果

## Acceptance Criteria

### AC-1: 前端UI显示按章节拆分Markdown开关
- **Given**: 用户打开PDF翻译工具网页
- **When**: 查看翻译表单
- **Then**: 表单中显示"按章节拆分Markdown"的复选框
- **Verification**: `human-judgment`

### AC-2: 后端接收按章节拆分参数
- **Given**: 用户提交翻译请求
- **When**: 选择或取消选择"按章节拆分Markdown"选项
- **Then**: 后端正确接收该参数值
- **Verification**: `programmatic`

### AC-3: 选择按章节拆分时生成章节Markdown文件
- **Given**: 用户选择"按章节拆分Markdown"选项并提交翻译请求
- **When**: 翻译完成后
- **Then**: 生成按章节拆分的Markdown文件和包含所有章节的zip文件
- **Verification**: `programmatic`

### AC-4: 不选择按章节拆分时生成单一Markdown文件
- **Given**: 用户取消选择"按章节拆分Markdown"选项并提交翻译请求
- **When**: 翻译完成后
- **Then**: 生成单一的Markdown文件
- **Verification**: `programmatic`

### AC-5: 不选择按章节拆分时不执行章节提取分析
- **Given**: 用户取消选择"按章节拆分Markdown"选项并提交翻译请求
- **When**: 系统处理翻译任务时
- **Then**: 不执行章节相关的提取分析代码
- **Verification**: `programmatic`

## Open Questions
- [x] 按章节拆分功能是否应该默认开启？ - 是的，默认开启
- [x] 是否需要在UI上添加关于按章节拆分功能的说明文本？ - 是的，添加说明文本