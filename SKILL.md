---
name: "pdftrans"
description: "PDF翻译工具命令行界面，支持翻译PDF文件、提取术语表和列出支持的语言。当用户需要翻译PDF文件、提取术语表、查询支持的语言，或者处理任何PDF相关的翻译任务时，务必使用此工具。即使用户没有明确提到'pdftrans'，只要涉及PDF翻译、术语提取或'pdftrans'支持语言查询，都应该使用此工具。"
---

# PDF翻译工具 (pdftrans)

## 功能概述

pdftrans是一个支持多翻译API的PDF翻译命令行工具，你必须根据用户需求选择合适的参数调用工具：
- 翻译PDF文件为目标语言
- 从PDF文件中提取术语表
- 列出pdftrans支持的语言代码和名称

**执行规则：**
- 如果用户没有指定语言，自动检查输入文件的前100行，根据内容判断源语言。默认目标语言为中文。
- **默认输出格式：Markdown（按章节切分），启用语义合并和LLM合并**
- 如果用户没有指定输出格式，默认生成 Markdown 格式输出，自动按章节切分
- 如果用户没有指定选项，默认启用语义合并（-m）和LLM合并（-l）以提高翻译质量

## 支持的输出格式
- pdf：生成PDF格式输出
- docx：生成Word文档格式输出
- markdown：生成Markdown格式输出（打包为zip文件）

## 智能后缀处理
工具会根据输出格式自动添加正确的文件后缀：
- Markdown格式自动添加 `.zip` 后缀
- PDF格式自动添加 `.pdf` 后缀
- Word格式自动添加 `.docx` 后缀

## 输出说明

**默认行为：**
- **默认输出格式：Markdown（按章节切分）**
- **默认启用语义合并（-m）和LLM合并（-l）**
- 如果用户没有指定输出目录，默认输出到原文件所在目录

**临时目录：**
- 工具会在输出目录下自动创建 `tmp` 子目录
- 临时文件（如提取的图片、中间文档）会存放在 `tmp` 目录中
- `tmp` 目录中的文件可供调试使用

**输出文件名：**
- 用户可通过 `-o` 参数指定输出文件名，支持所有输出格式（PDF、DOCX、Markdown）
- 如果用户没有指定输出文件名，将生成结果保存为以下格式：默认输出文件名与输入文件名相同，加上前缀 "translated_" 或 "glossary_"
- 如果指定了页码范围，在文件名中包含页码范围
- 示例：`-o custom_name.pdf` 或 `-o custom_name.zip`

## API密钥配置

pdftrans工具需要配置翻译API的API密钥才能正常工作。目前支持两种翻译服务：
1. **aiping API** （默认）
2. **硅基流动 API**

**配置步骤：**
1. 复制 `.env.example` 文件为 `.env`
2. 编辑 `.env` 文件，添加以下配置：

```bash
# .env 文件示例

# aiping API 配置
AIPING_API_KEY=your_aiping_api_key

# 硅基流动 API 配置
SILICON_FLOW_API_KEY=your_silicon_flow_api_key
```

**注意：** 只需配置其中一种翻译服务的API密钥即可使用。

## 命令行使用

使用 `pdftrans -h` 查看详细使用帮助。

### 翻译使用示例

```bash
# 基本翻译
pdftrans translate document.pdf -o translated.pdf

# 指定语言和翻译服务
pdftrans translate document.pdf -s en -t zh -T silicon_flow

# 指定页码范围和输出格式
pdftrans translate document.pdf --pages "1-10,15" -f docx

# 启用语义合并和LLM合并
pdftrans translate document.pdf -m -l

# 按章节拆分输出Markdown
pdftrans translate document.pdf -f markdown -c
```

### 提取术语表使用示例

```bash
# 提取术语表
pdftrans glossary document.pdf -o glossary.txt

# 指定语言和页码范围
pdftrans glossary document.pdf -s en -t zh --pages "1-20"
```

### 列出支持的语言使用示例

**功能**：显示所有支持的语言代码和名称

```bash
# 列出支持的语言
pdftrans list-languages
```

## 支持的语言

- zh（中文）
- en（英语）
- ja（日语）
- ko（韩语）
- fr（法语）
- de（德语）
- es（西班牙语）
- ru（俄语）


## 支持的翻译服务

- aiping：使用aiping翻译API
- silicon_flow：使用硅基流动翻译API


## 注意事项

1. 输入文件必须是PDF格式
2. 翻译服务需要配置相应的API密钥
3. 大文件翻译可能需要较长时间
4. 语义合并和LLM合并会增加翻译时间，但能提高翻译质量
5. 按章节拆分功能只在选择Markdown输出格式时起作用

## 错误处理

### 权限问题

如果翻译过程中遇到输出目录权限错误（如 `Operation not permitted` 或 `PermissionError`），说明当前环境没有写入权限。此时应：
1. **立即停止尝试**，不要重复执行命令
2. 告知用户权限问题，建议用户手动执行翻译命令或更换输出目录
3. 权限问题通常出现在沙盒环境或受保护的系统目录中

### 其他常见错误

- **API密钥错误**：确保已在 `.env` 文件中正确配置了API密钥
- **文件格式错误**：确保输入文件是有效的PDF格式
- **网络错误**：检查网络连接是否正常，翻译服务是否可访问
- **参数错误**：使用 `pdftrans -h` 查看正确的参数格式