# 翻译后格式排版开关 Spec

## Why
`format_blocks`（LLM 格式排版）目前无条件对所有输出格式执行，但它主要是为 PDF 渲染优化文本格式（标点规范、中英混排间距等）。输出 DOCX 或 Markdown 时，这些排版调整既不必要又浪费 API 调用。需要添加开关控制是否执行格式排版，且默认仅 PDF 输出时启用。

## What Changes
- 在 config.py 中添加 `ENABLE_FORMAT_BLOCKS` 配置项（环境变量，默认 `false`）
- `auto` 模式下：仅当输出格式包含 PDF 时才调用 `format_blocks`
- 默认关闭，用户需显式启用
- 在 `translation_content.py` 中根据配置和输出格式决定是否执行 `format_blocks`
- 在 `.env.example` 中添加配置说明

## Impact
- Affected code: `config.py`（新增配置项）
- Affected code: `services/translation_content.py`（`_translate_content` 方法中 format_blocks 调用处，约第 141-176 行）
- Affected code: `.env.example`（添加配置说明）

## ADDED Requirements

### Requirement: 格式排版开关配置
系统 SHALL 提供环境变量 `ENABLE_FORMAT_BLOCKS` 控制是否执行 LLM 格式排版，支持三个值：

| 值 | 行为 |
|---|------|
| `false`（默认） | 不执行 format_blocks |
| `true` | 始终执行 format_blocks |
| `auto` | 仅当输出格式包含 PDF 时执行 format_blocks |

#### Scenario: 默认（不设置环境变量）+ PDF 输出
- **WHEN** 未设置 `ENABLE_FORMAT_BLOCKS` 且输出格式为 `pdf`
- **THEN** 跳过 format_blocks（默认关闭）

#### Scenario: true + 任意输出格式
- **WHEN** `ENABLE_FORMAT_BLOCKS=true` 且输出格式为 `markdown`
- **THEN** 执行 format_blocks（强制开启）

#### Scenario: auto + PDF 输出
- **WHEN** `ENABLE_FORMAT_BLOCKS=auto` 且输出格式为 `pdf`
- **THEN** 执行 format_blocks

#### Scenario: auto + DOCX 输出
- **WHEN** `ENABLE_FORMAT_BLOCKS=auto` 且输出格式为 `docx`
- **THEN** 跳过 format_blocks

#### Scenario: auto + pdf_docx 输出
- **WHEN** `ENABLE_FORMAT_BLOCKS=auto` 且输出格式为 `pdf_docx`
- **THEN** 执行 format_blocks（因为包含 PDF）

### Requirement: format_blocks 调用条件判断
系统 SHALL 在 `translation_content.py` 的 `_translate_content` 方法中，根据 `ENABLE_FORMAT_BLOCKS` 配置和当前输出格式决定是否执行 format_blocks 循环。

需要将 `output_format` 参数传递到 `_translate_content` 方法中（当前该方法未接收此参数）。

#### Scenario: 跳过 format_blocks 时的日志
- **WHEN** 根据配置跳过 format_blocks
- **THEN** 记录 INFO 级别日志，说明跳过原因（如"输出格式为 docx，跳过格式排版"）

## MODIFIED Requirements

### Requirement: _translate_content 方法签名
`_translate_content` 方法需要接收 `output_format` 参数，以便判断是否需要执行 format_blocks。
