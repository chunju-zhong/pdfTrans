# 修复进度提示正确性 Spec

## Why
全面审查进度提示后发现 18 个问题，包括：CLI 的 progress_callback 百分比与 PHASE_CONFIG 严重不一致、glossary 任务显示"翻译完成"/"翻译已取消"、进度倒退（translation 5% 后又设 semantic_merge 0%）、clean 阶段消息说"翻译完成"、init 阶段被重复设置导致进度倒退等。用户看到的进度消息经常与实际操作不符。

## What Changes
- 移除 `process_translation_sync` 中与 PHASE_CONFIG 不一致的 `progress_callback` 硬编码百分比，改为从 task.progress 读取
- 修复 `set_result`、`cancel` 方法根据 task_type 显示正确消息
- 修复 `app.py` 中 glossary 错误处理使用 `set_error`
- 修复 `clean` 阶段消息为"临时文件清理完成"
- 移除 `_create_translators` 中不合理的 `translation` 0% 更新
- 修复进度倒退：移除 `_translate_content` 中 `translation` 5% 更新
- 跳过语义合并时不设 semantic_merge 100%，直接进入 translation
- 修复 glossary 服务中 init 阶段消息矛盾和重复设置
- 修复 app.py 和 CLI 中 init 阶段重复设置导致进度倒退

## Impact
- Affected code: `models/task.py`、`services/translation_service.py`、`services/glossary_service.py`、`app.py`、`cli/translate_command.py`、`cli/glossary_command.py`
- Affected specs: optimize-extraction-progress（补充修正）

## ADDED Requirements

### Requirement: progress_callback 与 PHASE_CONFIG 对齐
`process_translation_sync` 中的 `progress_callback` SHALL 从 `task.progress` 和 `task.message` 读取值，而非使用硬编码百分比。

#### Scenario: CLI 进度与 Web 进度一致
- **WHEN** CLI 模式下翻译进行到 extraction 阶段完成
- **THEN** progress_callback 报告的百分比与 task.progress 一致（约 40%），而非硬编码的 10%

### Requirement: 任务完成消息根据类型区分
`set_result` 和 `cancel` 方法 SHALL 根据 `task_type` 显示对应的消息。

#### Scenario: 术语提取任务完成
- **WHEN** glossary 任务完成
- **THEN** 消息显示"术语提取完成！"而非"翻译完成！"

#### Scenario: 术语提取任务取消
- **WHEN** glossary 任务被取消
- **THEN** 消息显示"术语提取已取消"而非"翻译已取消"

### Requirement: glossary 错误处理使用 set_error
`app.py` 中 glossary 路由的错误处理 SHALL 使用 `task.set_error()` 方法，确保 message 字段正确更新。

#### Scenario: 术语提取失败
- **WHEN** glossary 提取过程抛出异常
- **THEN** task.message 更新为"术语提取失败: ..."，而非保留上一次进度消息

### Requirement: clean 阶段消息正确
`clean` 阶段 100% 的消息 SHALL 描述清理操作完成，而非"翻译完成！"。

#### Scenario: 清理阶段完成
- **WHEN** clean 阶段进度更新到 100%
- **THEN** 消息显示"临时文件清理完成"

### Requirement: 进度不倒退
进度值 SHALL 单调递增，不允许从较高阶段回退到较低阶段。

#### Scenario: 语义合并前不设置 translation 阶段
- **WHEN** `_translate_content` 被调用且 semantic_merge=True
- **THEN** 不在语义合并之前设置 translation 阶段，避免从 52% 倒退到 40%

#### Scenario: 跳过语义合并时不设 semantic_merge 100%
- **WHEN** semantic_merge=False
- **THEN** 不设置 semantic_merge 阶段进度，直接进入 translation 阶段

### Requirement: init 阶段不重复设置
调用方（app.py、CLI）和被调用方（service）SHALL 不重复设置 init 阶段，避免进度倒退。

#### Scenario: Web 翻译任务
- **WHEN** app.py 设置 init 100% 后调用 process_translation
- **THEN** process_translation 不再重新设置 init 0%/50%/100%

#### Scenario: CLI 翻译任务
- **WHEN** CLI 设置 init 100% 后调用 process_translation_sync
- **THEN** process_translation_sync 不再重新设置 init 0%/50%/100%

### Requirement: glossary init 阶段消息正确
glossary 服务中 init 阶段 100% 的消息 SHALL 表示初始化完成，而非"开始提取..."。

#### Scenario: 术语提取初始化完成
- **WHEN** glossary init 阶段更新到 100%
- **THEN** 消息显示"初始化完成"而非"开始提取PDF文本..."

### Requirement: glossary pdf_extraction 阶段有起始进度
glossary 服务中 pdf_extraction 阶段 SHALL 在开始提取时设置 0% 进度，而非直接跳到 100%。

#### Scenario: 术语提取 PDF 文本开始
- **WHEN** 开始提取 PDF 文本
- **THEN** 先设置 pdf_extraction 0% "正在提取PDF文本..."，完成后再设 100%

## MODIFIED Requirements

### Requirement: _create_translators 不设置 translation 阶段
`_create_translators` 方法 SHALL 不设置 `translation` 阶段进度，因为创建翻译器不是翻译操作。

### Requirement: _translate_content 不预设 translation 阶段
`_translate_content` 方法 SHALL 不在调用 `translate_content` 之前设置 `translation` 5% 进度，避免与后续 semantic_merge 阶段冲突导致进度倒退。

### Requirement: extract_glossary_from_pdf 不重复设置 init 阶段
`extract_glossary_from_pdf` 和 `extract_glossary_sync` SHALL 不设置 `init` 阶段进度，因为调用方已经设置了。

### Requirement: glossary progress_callback 与 GLOSSARY_PHASE_CONFIG 对齐
`extract_glossary_sync` 中的 `progress_callback` SHALL 从 `task.progress` 读取值，而非使用硬编码百分比。
