# 添加CLI命令行支持 Spec

## Why
当前PDF翻译工具仅提供Web界面，用户需要通过浏览器上传文件并等待翻译完成。对于需要批量处理、自动化集成或服务器部署的场景，命令行界面(CLI)更加高效和灵活。添加CLI支持可以让用户：
1. 通过脚本批量处理PDF文件
2. 集成到自动化工作流中
3. 在无头服务器环境中使用
4. 更快速地执行翻译任务，无需启动Web服务

## What Changes
- 新增 `cli.py` - 命令行入口文件，使用Python标准库argparse实现
- 新增 `cli/` 目录 - 存放CLI相关模块
  - `cli/translate_command.py` - 翻译命令实现
  - `cli/glossary_command.py` - 术语提取命令实现
  - `cli/progress_display.py` - 进度显示组件
- 修改 `services/translation_service.py` - 添加同步翻译方法，支持CLI调用
- 修改 `requirements.txt` - 添加CLI相关依赖（如有需要）
- 新增 `pdftrans` 命令入口 - 通过setup.py或pyproject.toml配置

## Impact
- Affected specs: 无（新增功能）
- Affected code: 
  - services/translation_service.py（添加同步方法）
  - 新增 cli.py, cli/ 目录
  - requirements.txt（可能添加依赖）

## ADDED Requirements

### Requirement: CLI基础框架
The system SHALL provide a command-line interface using Python's built-in argparse module.

#### Scenario: 显示帮助信息
- **WHEN** 用户执行 `python cli.py --help` 或 `pdftrans --help`
- **THEN** 系统应显示所有可用命令和选项的帮助信息

#### Scenario: 命令结构
- **GIVEN** CLI支持子命令结构
- **THEN** 应包含以下子命令：
  - `translate` - 翻译PDF文件
  - `glossary` - 提取术语表
  - `list-languages` - 列出支持的语言

### Requirement: 翻译命令
The system SHALL provide a `translate` subcommand to translate PDF files.

#### Scenario: 基本翻译
- **GIVEN** 用户执行 `pdftrans translate input.pdf -o output.pdf`
- **WHEN** 源文件存在且格式正确
- **THEN** 系统应翻译PDF并保存到指定输出路径

#### Scenario: 指定语言
- **GIVEN** 用户执行 `pdftrans translate input.pdf --source en --target zh`
- **THEN** 系统应使用指定的源语言和目标语言进行翻译

#### Scenario: 指定翻译服务
- **GIVEN** 用户执行 `pdftrans translate input.pdf --translator silicon_flow`
- **THEN** 系统应使用指定的翻译服务（aiping/silicon_flow）

#### Scenario: 指定页码范围
- **GIVEN** 用户执行 `pdftrans translate input.pdf --pages "1-5,7,9-10"`
- **THEN** 系统应只翻译指定的页码范围

#### Scenario: 指定输出格式
- **GIVEN** 用户执行 `pdftrans translate input.pdf --format docx`
- **THEN** 系统应生成指定格式的输出文件（pdf/docx/markdown）

#### Scenario: 使用术语表
- **GIVEN** 用户执行 `pdftrans translate input.pdf --glossary glossary.txt`
- **THEN** 系统应使用指定的术语表文件进行翻译

#### Scenario: 启用语义合并
- **GIVEN** 用户执行 `pdftrans translate input.pdf --semantic-merge`
- **THEN** 系统应启用语义合并功能

#### Scenario: 按章节拆分
- **GIVEN** 用户执行 `pdftrans translate input.pdf --chapter-split`
- **THEN** 系统应按章节拆分生成多个输出文件

#### Scenario: 显示进度
- **GIVEN** 翻译任务正在执行
- **WHEN** 用户使用 `--verbose` 或 `-v` 选项
- **THEN** 系统应在终端显示实时进度信息

### Requirement: 术语提取命令
The system SHALL provide a `glossary` subcommand to extract glossary from PDF files.

#### Scenario: 基本术语提取
- **GIVEN** 用户执行 `pdftrans glossary input.pdf -o glossary.txt`
- **WHEN** 源文件存在且格式正确
- **THEN** 系统应提取术语表并保存到指定文件

#### Scenario: 指定页码范围
- **GIVEN** 用户执行 `pdftrans glossary input.pdf --pages "1-10"`
- **THEN** 系统应只从指定页码范围提取术语

### Requirement: 语言列表命令
The system SHALL provide a `list-languages` subcommand to display supported languages.

#### Scenario: 显示支持的语言
- **GIVEN** 用户执行 `pdftrans list-languages`
- **THEN** 系统应显示所有支持的语言代码和名称

### Requirement: 配置支持
The system SHALL support configuration through environment variables and .env files.

#### Scenario: 使用环境变量
- **GIVEN** 用户已设置 `AIPING_API_KEY` 或 `SILICON_FLOW_API_KEY` 环境变量
- **WHEN** 执行CLI命令
- **THEN** 系统应使用环境变量中的API密钥

#### Scenario: 使用.env文件
- **GIVEN** 工作目录存在 `.env` 文件
- **WHEN** 执行CLI命令
- **THEN** 系统应自动加载.env文件中的配置

## MODIFIED Requirements
无

## REMOVED Requirements
无

## CLI命令规范

### 命令格式
```
pdftrans <command> [options] <arguments>
```

### 全局选项
- `-h, --help` - 显示帮助信息
- `-v, --verbose` - 显示详细输出
- `--version` - 显示版本信息

### translate 命令选项
| 选项 | 短选项 | 必需 | 默认值 | 可选项 | 说明 |
|------|--------|------|--------|--------|------|
| --output | -o | 否 | 自动生成 | - | 输出文件路径 |
| --source | -s | 否 | en | zh, en, ja, ko, fr, de, es, ru | 源语言代码 |
| --target | -t | 否 | zh | zh, en, ja, ko, fr, de, es, ru | 目标语言代码 |
| --translator | -T | 否 | aiping | aiping, silicon_flow | 翻译服务类型 |
| --pages | -p | 否 | 全部 | - | 页码范围，如"1-5,7,9-10" |
| --format | -f | 否 | pdf | pdf, docx, markdown | 输出格式 |
| --glossary | -g | 否 | 无 | - | 术语表文件路径 |
| --doc-type | -d | 否 | AI技术 | 任意字符串 | 文档类型或领域说明（如：AI技术、技术文档、商务文档、医学论文等） |
| --semantic-merge | -m | 否 | False | - | 启用语义合并 |
| --llm-merge | -l | 否 | False | - | 使用LLM合并 |
| --chapter-split | -c | 否 | False | - | 按章节拆分输出Markdown，只在选择Markdown输出格式时起作用 |

### glossary 命令选项
| 选项 | 短选项 | 必需 | 默认值 | 可选项 | 说明 |
|------|--------|------|--------|--------|------|
| --output | -o | 否 | 自动生成 | - | 输出文件路径 |
| --source | -s | 否 | en | zh, en, ja, ko, fr, de, es, ru | 源语言代码 |
| --target | -t | 否 | zh | zh, en, ja, ko, fr, de, es, ru | 目标语言代码 |
| --translator | -T | 否 | aiping | aiping, silicon_flow | 翻译服务类型 |
| --pages | -p | 否 | 全部 | - | 页码范围，如"1-5,7,9-10" |
| --doc-type | -d | 否 | AI技术 | 任意字符串 | 文档类型或领域说明（如：AI技术、技术文档、商务文档、医学论文等） |

## 使用示例

### 基本翻译
```bash
pdftrans translate document.pdf -o translated.pdf
```

### 指定语言和翻译服务
```bash
pdftrans translate document.pdf -s en -t zh -T silicon_flow -o output.pdf
```

### 翻译指定页码
```bash
pdftrans translate document.pdf --pages "1-10,15,20-25" -o output.pdf
```

### 生成Word文档
```bash
pdftrans translate document.pdf -f docx -o output.docx
```

### 使用术语表
```bash
pdftrans translate document.pdf -g glossary.txt -o output.pdf
```

### 启用语义合并
```bash
pdftrans translate document.pdf --semantic-merge -o output.pdf
```

### 指定文档类型
```bash
pdftrans translate document.pdf -d "机器学习论文" -o output.pdf
```

### 按章节拆分输出
```bash
pdftrans translate document.pdf --chapter-split -o output/
```

### 提取术语表
```bash
pdftrans glossary document.pdf -o glossary.txt
```

### 显示支持的语言
```bash
pdftrans list-languages
```
