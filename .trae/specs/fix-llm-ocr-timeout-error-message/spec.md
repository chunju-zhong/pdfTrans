# 修复 LLM-OCR 请求超时错误提示不准确 Spec

## Why
运行后翻译 PDF 第 6 页时没有文本内容。实际原因是 LLM-OCR API 请求超时（`httpx.ReadTimeout`），但错误仅记录为 "Request timed out."，下游层层静默吞没后最终显示为 "没有找到需要翻译的文本块"。用户无法得知实际原因是 API 超时，而非页面无内容。

## What Changes
- `_extract_page` 中超时时区分 `APITimeoutError` 并给出中文可读错误消息
- 超时错误向上冒泡，在 `extract_from_pdf` 中通过 `progress_callback` 传达到任务状态
- `translation_service` 中当提取结果为 0 且存在超时/错误原因时，使用具体错误消息而非通用 "没有找到需要翻译的文本块"
- 为超时添加重试机制：单页 OCR 请求超时时最多重试 1 次

## Impact
- Affected specs: fix-ocr-batch-failure-silent-swallow（缺失页码追踪机制可复用）
- Affected code: `modules/ocr/llm_extractor.py`、`services/translation_service.py`

## ADDED Requirements

### Requirement: 超时错误中文可读消息
系统 SHALL 在 LLM-OCR API 请求超时时，记录包含超时信息和推荐行动的中文错误消息，而非原始的 "Request timed out."。

#### Scenario: API 请求超时
- **WHEN** `self.client.chat.completions.create()` 抛出 `APITimeoutError`
- **THEN** 错误消息为 "LLM OCR API 请求超时（120秒），请检查网络连接或 API 服务状态，建议稍后重试或使用非 LLM OCR 引擎"
- **AND** 错误日志中包含实际超时时间、页码和模型名称

#### Scenario: 非超时异常
- **WHEN** 其他异常（如 JSON 解析错误、网络连接拒绝）
- **THEN** 保持原有错误消息格式不变

### Requirement: 超时重试机制
系统 SHALL 在单页 OCR API 请求因超时而失败时，自动重试 1 次。

#### Scenario: 首次超时后重试
- **WHEN** 第 N 页 OCR 请求首次超时
- **THEN** 记录警告日志 "第 N 页首次请求超时，正在进行第 1 次重试"
- **AND** 重试该页的 OCR 请求
- **AND** 重试使用相同的参数（不降级）

#### Scenario: 重试成功
- **WHEN** 重试的请求成功返回
- **THEN** 正常处理该页结果

#### Scenario: 重试仍然超时
- **WHEN** 重试的请求也超时
- **THEN** 记录错误 "第 N 页 OCR 请求重试后仍然超时，放弃该页"
- **AND** 该页返回空结果

### Requirement: 超时错误向上传播到任务状态
系统 SHALL 在 OCR 提取阶段发生超时错误时，通过 `task.add_warning()` 和 `task.update_phase_progress()` 将具体原因传播到任务状态。

#### Scenario: 单页 OCR 超时
- **WHEN** 某页 OCR 请求超时（重试后仍失败）
- **THEN** 调用 `task.add_warning("第 6 页 LLM OCR 提取超时，该页内容可能缺失", context={"process": "extraction", "page": 6})`
- **AND** `task.update_phase_progress('extraction', 100, '提取完成，第 6 页 OCR 超时')` 中的消息反映超时信息

#### Scenario: 无超时正常完成
- **WHEN** 所有页 OCR 正常完成
- **THEN** 保持现有行为不变

### Requirement: 提取结果为 0 时使用具体错误原因
当提取结果为空且有记录的错误原因时，`translation_service` 中的日志和任务状态消息 SHALL 反映具体原因而非通用消息。

#### Scenario: 提取结果为空且有超时错误
- **WHEN** 所有页 OCR 均因超时而失败，提取结果为 0 块
- **THEN** 记录错误日志 "所有目标页面 OCR 提取均因超时而失败，请检查网络或 API 服务"
- **AND** `task.set_error("OCR 提取失败：API 请求超时，请检查网络连接或 API 服务状态")`
- **AND** 不继续后续翻译步骤

#### Scenario: 提取结果为空但无错误记录
- **WHEN** 提取结果为空但过程中无错误记录
- **THEN** 保持现有行为不变

## MODIFIED Requirements

### Requirement: _extract_page 超时异常处理精细化
`_extract_page` 中的 `except Exception` 块拆分为：
1. 先捕获 `openai.APITimeoutError`（含 `httpx.ReadTimeout`），生成可读中文错误消息
2. 再捕获其他 `Exception`，保持原有错误格式
