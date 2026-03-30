# CLI临时目录管理 Spec

## Why
在命令行模式下，当用户使用 `-o` 参数指定输出目录时，需要在指定目录下创建 `tmp` 子目录来存放生成过程中产生的临时文件（如提取的图片、中间翻译文档等），最后再将最终结果移动到 `-o` 指定的位置和文件名。这样可以：
1. 保持生成过程的文件组织清晰
2. 避免临时文件污染输出目录
3. 便于调试和查看中间结果

## What Changes
- 在 `-o` 指定的目录下自动创建 `tmp` 子目录
- 将所有生成过程中的临时文件（提取的图片、中间文档等）存放到 `tmp` 目录
- 生成完成后，将最终结果移动到 `-o` 指定的位置和文件名
- 保留 `tmp` 目录中的文件供调试使用

## Impact
- Affected specs: output_directory_fix, image_extraction_fix
- Affected code: 
  - cli/translate_command.py
  - cli/glossary_command.py
  - services/translation_service.py
  - services/glossary_service.py
  - modules/pdf_extractor.py

## ADDED Requirements

### Requirement: CLI临时目录管理
The system SHALL provide a temporary directory management mechanism for CLI mode.

#### Scenario: 用户指定输出目录
- **GIVEN** 用户在命令行使用 `-o` 参数指定了输出路径
- **WHEN** 翻译过程开始
- **THEN** 系统应在输出目录下创建 `tmp` 子目录
- **AND** 将所有临时文件（提取的图片、中间文档）存放到 `tmp` 目录
- **AND** 生成完成后将最终结果移动到 `-o` 指定的位置

#### Scenario: 未指定输出目录
- **GIVEN** 用户未在命令行指定输出路径
- **WHEN** 翻译过程开始
- **THEN** 系统使用默认的 `outputs` 目录
- **AND** 在 `outputs` 目录下创建 `tmp` 子目录
- **AND** 按上述规则管理临时文件

#### Scenario: 临时目录已存在
- **GIVEN** `tmp` 目录已存在
- **WHEN** 翻译过程开始
- **THEN** 系统应清理或重用现有 `tmp` 目录
- **AND** 确保不会残留之前任务的文件

#### Scenario: 术语提取命令
- **GIVEN** 用户使用 `glossary` 子命令并指定了 `-o` 参数
- **WHEN** 术语提取过程开始
- **THEN** 系统应在输出目录下创建 `tmp` 子目录
- **AND** 将提取过程中产生的临时文件存放到 `tmp` 目录
- **AND** 最终将术语表保存到 `-o` 指定的位置

## MODIFIED Requirements

### Requirement: 图像提取目录
**Current**: 图像提取到输出目录或默认目录
**Modified**: 图像提取到 `tmp` 子目录

### Requirement: 输出生成
**Current**: 直接生成到指定输出路径
**Modified**: 先生成到 `tmp` 目录，完成后移动到最终位置
