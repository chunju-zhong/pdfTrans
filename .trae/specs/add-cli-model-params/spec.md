# 增加命令行模型参数 Spec

## Why

当前翻译模型、LAYOUT排版模型、GLOSSARY模型、OCR LLM 模型的名字只能通过 `.env` 环境变量配置，无法在命令行中临时指定。用户需要在不同任务中使用不同模型时，必须手动修改 `.env` 文件，使用不便。

## What Changes

- 为 `translate` 子命令新增 4 个可选参数：`--translation-model`、`--layout-model`、`--glossary-model`、`--ocr-llm-model`
- 为 `glossary` 子命令新增 1 个可选参数：`--glossary-model`
- 参数值覆盖对应服务商（aiping/silicon_flow）的模型配置，仅在命令行指定时生效，不影响 `.env` 配置
- 修改 `cli.py`、`cli/translate_command.py`、`cli/glossary_command.py` 以接收和传递新参数
- 修改 `services/translation_service.py` 在 `process_translation_sync` 中接受并传递模型参数
- 修改 `services/glossary_service.py` 在 `extract_glossary_sync` 中接受并传递 glossary 模型参数
- 修改 `modules/glossary_extractor.py` 的 `create_glossary_extractor()` 函数以接受模型参数
- 不影响现有 Web 界面行为

## Impact

- Affected specs: CLI 参数规范、翻译服务接口、术语提取服务接口
- Affected code: `cli.py`, `cli/translate_command.py`, `cli/glossary_command.py`, `services/translation_service.py`, `services/glossary_service.py`, `modules/glossary_extractor.py`

## ADDED Requirements

### Requirement: CLI 翻译子命令模型参数

The system SHALL allow users to specify model names via CLI parameters for the `translate` subcommand.

#### Scenario: 指定翻译模型
- **WHEN** 用户执行 `pdftrans translate input.pdf --translation-model GLM-5.1`
- **THEN** 翻译过程中使用指定的 `GLM-5.1` 作为翻译模型（根据 `--translator` 类型选择对应的服务商）
- **AND** 不影响 `.env` 文件中的 `AIPING_MODEL_TRANSLATION` 或 `SILICON_FLOW_MODEL_TRANSLATION` 配置

#### Scenario: 指定排版模型
- **WHEN** 用户执行 `pdftrans translate input.pdf --layout-model Qwen3-32B`
- **THEN** Markdown 排版过程中使用指定的 `Qwen3-32B` 作为布局模型

#### Scenario: 指定术语提取模型
- **WHEN** 用户执行 `pdftrans translate input.pdf --glossary-model Qwen3-32B`
- **THEN** 术语提取过程中使用指定的 `Qwen3-32B` 作为术语提取模型

#### Scenario: 指定 OCR LLM 模型
- **WHEN** 用户执行 `pdftrans translate input.pdf --ocr --ocr-engine llm --ocr-llm-model DeepSeek-OCR`
- **THEN** LLM OCR 过程中使用指定的 `DeepSeek-OCR` 作为 OCR 模型

#### Scenario: 同时指定多个模型
- **WHEN** 用户执行 `pdftrans translate input.pdf --translation-model GLM-5.1 --layout-model Qwen3-32B --glossary-model Qwen3-32B --ocr-llm-model DeepSeek-OCR`
- **THEN** 各模块分别使用对应的指定模型

#### Scenario: 不指定模型参数（保持默认）
- **WHEN** 用户执行 `pdftrans translate input.pdf` 不传递任何 `--*-model` 参数
- **THEN** 各模块使用 `.env` 或 `config.py` 中的默认模型配置，行为不变

### Requirement: CLI 术语子命令模型参数

The system SHALL allow users to specify glossary model name via CLI parameter for the `glossary` subcommand.

#### Scenario: 指定术语提取模型
- **WHEN** 用户执行 `pdftrans glossary input.pdf --glossary-model Qwen3-32B`
- **THEN** 术语提取过程中使用指定的 `Qwen3-32B` 作为术语提取模型

## MODIFIED Requirements

无修改的需求。

## REMOVED Requirements

无移除的需求。
