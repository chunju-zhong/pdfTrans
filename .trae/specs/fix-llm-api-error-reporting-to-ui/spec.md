# LLM API 错误分类与 UI 上报 Spec

## 调查范围：12 个 LLM API 直接调用点清单

| # | 文件:行号 | 用途 | 当前异常处理 | 是否上报 UI | 静默吞没 |
|---|----------|------|--------------|------------|---------|
| 1 | [modules/ocr/llm_extractor.py:438](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_extractor.py#L438) | LLM OCR 文本提取 | `APITimeoutError` + 通用 `Exception` | 是（`progress_callback('page_error')`） | 否 |
| 2 | [modules/translator.py:189](file:///Users/chunju/work/pdfTrans/modules/translator.py#L189) | 翻译后格式排版 `format_blocks`（流式） | 仅通用 `Exception` | 否 | **是**（返回原文） |
| 3 | [modules/silicon_flow_translator.py:87](file:///Users/chunju/work/pdfTrans/modules/silicon_flow_translator.py#L87) | 硅基流动翻译（流式） | 通用 `Exception` 重新抛出 | 否（向上抛） | 否 |
| 4 | [modules/qianfan_translator.py:89](file:///Users/chunju/work/pdfTrans/modules/qianfan_translator.py#L89) | 百度千帆翻译（流式） | 通用 `Exception` 重新抛出 | 否（向上抛） | 否 |
| 5 | [modules/aiping_translator.py:92](file:///Users/chunju/work/pdfTrans/modules/aiping_translator.py#L92) | aiping 翻译（流式，含 3 次重试） | 通用 `Exception` 重新抛出 | 否（向上抛） | 否 |
| 6 | [modules/semantic_analyzer.py:104](file:///Users/chunju/work/pdfTrans/modules/semantic_analyzer.py#L104) | 单文本语义分析（非流式） | 仅通用 `Exception` | 否 | **是**（返回 `False`） |
| 7 | [modules/semantic_analyzer.py:206](file:///Users/chunju/work/pdfTrans/modules/semantic_analyzer.py#L206) | 批量语义分析（含 3 次重试） | `JSONDecodeError` + 通用 `Exception` | 否 | **是**（返回 `[False]*n`） |
| 8 | [modules/aiping_semantic_analyzer.py:58](file:///Users/chunju/work/pdfTrans/modules/aiping_semantic_analyzer.py#L58) | aiping 单语义分析（流式，含 3 次重试） | 仅通用 `Exception` | 否 | **是**（返回 `False`） |
| 9 | [modules/aiping_semantic_analyzer.py:168](file:///Users/chunju/work/pdfTrans/modules/aiping_semantic_analyzer.py#L168) | aiping 批量语义分析（流式，含 3 次重试） | `JSONDecodeError` + 通用 `Exception` | 否 | **是**（返回 `[False]*n`） |
| 10 | [modules/glossary_extractor.py:145](file:///Users/chunju/work/pdfTrans/modules/glossary_extractor.py#L145) | 术语提取（非流式） | 仅通用 `Exception` | 否 | **是**（返回 `""`） |
| 11 | [modules/markdown_generator.py:187](file:///Users/chunju/work/pdfTrans/modules/markdown_generator.py#L187) | 基础布局/Markdown `_call_api`（流式） | 无 try/except（外层 3 次重试） | 是（外层 `add_warning`） | 否 |
| 12 | [modules/markdown_generator.py:1344](file:///Users/chunju/work/pdfTrans/modules/markdown_generator.py#L1344) | aiping 布局 `_call_api`（流式） | 无 try/except（同上） | 是（同 #11） | 否 |

**静默吞没点共 6 个直接调用点（#2、#6、#7、#8、#9、#10）**，另有 4 个服务层编排点
（`translation_content.py:155`、`translation_table.py:87/311`、`glossary_service.py:91/130`）
也仅 `logger.error` 不上报 UI，共 **10 个静默吞没点**需修复。

## Why

项目中共有 **12 个 LLM API 直接调用点**（OCR 提取、翻译、术语提取、语义分析、Markdown 排版），
当前错误处理存在两类问题：

### 问题 1：错误消息技术化、用户无法操作

以 `paddleocr-vl-0.9b` 触发的 400 错误为例（[modules/ocr/llm_extractor.py:488](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_extractor.py#L488)）：
```
LLM OCR API 请求失败: Error code: 400 - {'error': {'code': 'invalid_argument',
'message': 'parameter check failed, max_tokens range is [1, 4096]',
'type': 'invalid_request_error'}, 'id': 'as-ipn6ke2ufe'}
```
充斥 JSON、error code、id 等技术细节，普通用户无法识别这是 `max_tokens` 超限、需要调整
`OCR_LLM_MAX_TOKENS` 环境变量。同类问题存在于所有 12 个调用点——均使用 `str(e)` 原样输出。

### 问题 2：多个调用点静默吞没错误，UI 完全无感知

调查发现 **10 个调用点** 在 LLM 调用失败时仅 `logger.error`/`logger.warning` 后返回默认值
（原文、`False`、`""`），不向 UI 上报，用户看到的只是「翻译质量下降」「术语表缺失」
「排版未应用」等下游症状，无法定位根因是 LLM 调用失败。典型如：

| 调用点 | 静默行为 | 用户感知 |
|--------|---------|---------|
| [modules/translator.py:189](file:///Users/chunju/work/pdfTrans/modules/translator.py#L189) `format_blocks` | 返回未排版原文 | 译文无格式 |
| [modules/semantic_analyzer.py:104](file:///Users/chunju/work/pdfTrans/modules/semantic_analyzer.py#L104) | 返回 `False` | 跨页合并不生效 |
| [modules/glossary_extractor.py:145](file:///Users/chunju/work/pdfTrans/modules/glossary_extractor.py#L145) | 返回 `""` | 术语表丢失 |
| [services/translation_table.py:87-119](file:///Users/chunju/work/pdfTrans/services/translation_table.py#L87) | 回退原文 | 表格未翻译 |

### 问题 3：异常类型信息丢失

3 个翻译模块（[silicon_flow_translator.py:87](file:///Users/chunju/work/pdfTrans/modules/silicon_flow_translator.py#L87)、
[qianfan_translator.py:89](file:///Users/chunju/work/pdfTrans/modules/qianfan_translator.py#L89)、
[aiping_translator.py:92](file:///Users/chunju/work/pdfTrans/modules/aiping_translator.py#L92)）将所有异常
包成通用 `Exception(...)` 重新抛出，丢失 `AuthenticationError`/`RateLimitError`/`BadRequestError`
等类型信息，顶层 [services/translation_service.py:270](file:///Users/chunju/work/pdfTrans/services/translation_service.py#L270)
只能用 `f"翻译失败: {str(e)}"` 兜底，无法给出精准提示。

### 需要处理的 LLM API 错误类型（除 max_tokens 外）

| 异常类型 | HTTP | 根因 | 用户提示要点 |
|---------|------|------|------------|
| `AuthenticationError` | 401 | API key 无效/过期/额度耗尽 | 检查密钥配置 |
| `RateLimitError` | 429 | 频率/配额超限 | 稍后重试或更换密钥 |
| `BadRequestError` | 400 | 参数错误（max_tokens 超限、上下文超长、模型名错误） | 检查参数配置 |
| `APITimeoutError` | — | 网络或服务端慢 | 检查网络或重试 |
| `APIConnectionError` | — | DNS/网络/防火墙 | 检查网络/代理 |
| `InternalServerError` | 5xx | 服务端故障 | 稍后重试 |

## What Changes

### 新增共享错误处理工具

- **新增** `modules/llm_error_handler.py`：LLM API 错误分类工具
  - `classify_llm_error(e)` 函数：接收任意 `Exception`，返回 `{'category', 'user_message', 'is_retryable', 'original_message'}`
  - 覆盖 6 类 OpenAI 异常 + 通用兜底
  - 对 `BadRequestError` 特别检测 `max_tokens` 关键字，追加 `OCR_LLM_MAX_TOKENS`/`GLOSSARY_MAX_TOKENS` 等配置项调整建议
  - 返回中文用户友好消息，包含可操作建议

### 增强所有 12 个 LLM 调用点的错误消息

- `modules/ocr/llm_extractor.py` — 新增 `except BadRequestError` 分支，使用 `classify_llm_error` 生成提示
- `modules/translator.py` — `format_blocks` 异常处理使用 `classify_llm_error`
- `modules/silicon_flow_translator.py` / `qianfan_translator.py` / `aiping_translator.py` — 重新抛出时保留原始异常类型，附加友好消息
- `modules/semantic_analyzer.py` / `aiping_semantic_analyzer.py` — 异常处理使用 `classify_llm_error`
- `modules/glossary_extractor.py` — 异常处理使用 `classify_llm_error`
- `modules/markdown_generator.py` — `_call_api` 异常处理使用 `classify_llm_error`

### 修复 10 个静默吞没点，增加 UI 上报

- `services/translation_content.py:155-166`（`format_blocks` 调用处）— 增加 `task.add_warning`
- `services/translation_table.py:87-119`（表格行翻译汇总）— 增加 `task.add_warning`
- `services/translation_table.py:311-325`（表格行翻译 fallback）— 增加 `task.add_warning`
- `services/glossary_service.py:91-96`（术语提取逐页）— 增加 `task.add_warning`
- `services/glossary_service.py:130-132`（术语提取整体）— 增加 `task.add_warning`
- `modules/semantic_analyzer.py` / `aiping_semantic_analyzer.py` — 静默返回前增加 `logger.error`（语义分析为可选优化，失败时不影响主流程，仅增强日志）

### 不修改项

- **不修改** `config.py` 中任何默认值（`OCR_LLM_MAX_TOKENS=8000` 等保持不变，遵守既有 spec 约束）
- **不修改** API 调用参数（不做 `max_tokens` 钳制，由用户自行配置）
- **不修改** prompt 构建、`extra_body`、`temperature` 等业务逻辑
- **不修改** 已正确上报 UI 的调用点（如 `process_merged_blocks`、`markdown_generator` 外层）的上报机制，仅增强其错误消息内容

## Impact

- Affected specs:
  - `fix-llm-ocr-error-propagation` — 复用其 `progress_callback('page_error', ...)` 机制，本 spec 增强错误消息内容
  - `fix-llm-ocr-tibetan-penalty-regression` — 保持 `OCR_LLM_MAX_TOKENS=8000` 默认值不变
  - `add-baidu-qianfan-platform` — 改善千帆平台各类错误的用户可读性
  - `fix-llm-ocr-timeout-error-message` — 复用其超时错误处理模式，本 spec 扩展到更多错误类型
- Affected code:
  - **新增** `modules/llm_error_handler.py`
  - `modules/ocr/llm_extractor.py` — 异常处理增强
  - `modules/translator.py` — `format_blocks` 异常处理增强
  - `modules/silicon_flow_translator.py` / `qianfan_translator.py` / `aiping_translator.py` — 异常类型保留
  - `modules/semantic_analyzer.py` / `aiping_semantic_analyzer.py` — 异常处理增强
  - `modules/glossary_extractor.py` — 异常处理增强
  - `modules/markdown_generator.py` — `_call_api` 异常处理增强
  - `services/translation_content.py` — `format_blocks` 调用处增加 `task.add_warning`
  - `services/translation_table.py` — 表格翻译失败处增加 `task.add_warning`
  - `services/glossary_service.py` — 术语提取失败处增加 `task.add_warning`

## ADDED Requirements

### Requirement: LLM API 错误分类工具

系统 SHALL 在 `modules/llm_error_handler.py` 中提供 `classify_llm_error(e: Exception) -> dict`
函数，将 LLM API 异常分类为用户友好的中文消息。

#### Scenario: AuthenticationError (401)

- **WHEN** 异常为 `openai.AuthenticationError`
- **THEN** 返回 `{'category': 'auth', 'user_message': 'API 密钥无效或已过期，请检查 API Key 配置', 'is_retryable': False, ...}`
- **AND** `original_message` 保留原始 `str(e)`

#### Scenario: RateLimitError (429)

- **WHEN** 异常为 `openai.RateLimitError`
- **THEN** 返回 `{'category': 'rate_limit', 'user_message': '请求过于频繁或配额已用尽，请稍后重试或更换 API Key', 'is_retryable': True, ...}`

#### Scenario: BadRequestError 含 max_tokens

- **WHEN** 异常为 `openai.BadRequestError`
- **AND** `str(e).lower()` 包含 `max_tokens`
- **THEN** 返回 `{'category': 'bad_request_max_tokens', ...}`
- **AND** `user_message` SHALL 包含 `max_tokens 参数超限` 字样
- **AND** `user_message` SHALL 建议降低对应的环境变量（`OCR_LLM_MAX_TOKENS` / `GLOSSARY_MAX_TOKENS` / `LAYOUT_MAX_TOKENS`，根据调用上下文）

#### Scenario: BadRequestError 其他参数错误

- **WHEN** 异常为 `openai.BadRequestError`
- **AND** `str(e).lower()` 不包含 `max_tokens`
- **THEN** 返回 `{'category': 'bad_request', 'user_message': '请求参数错误：{原始消息摘要}', 'is_retryable': False, ...}`

#### Scenario: APITimeoutError

- **WHEN** 异常为 `openai.APITimeoutError`
- **THEN** 返回 `{'category': 'timeout', 'user_message': 'API 请求超时，请检查网络连接或重试', 'is_retryable': True, ...}`

#### Scenario: APIConnectionError

- **WHEN** 异常为 `openai.APIConnectionError`
- **THEN** 返回 `{'category': 'connection', 'user_message': '无法连接到 API 服务，请检查网络或代理设置', 'is_retryable': True, ...}`

#### Scenario: InternalServerError (5xx)

- **WHEN** 异常为 `openai.InternalServerError`
- **THEN** 返回 `{'category': 'server_error', 'user_message': 'API 服务端暂时不可用，请稍后重试', 'is_retryable': True, ...}`

#### Scenario: 未知异常

- **WHEN** 异常不属于上述任何类型
- **THEN** 返回 `{'category': 'unknown', 'user_message': 'API 调用失败：{原始消息}', 'is_retryable': False, ...}`

### Requirement: LLM OCR 调用点错误消息增强

系统 SHALL 在 `modules/ocr/llm_extractor.py` 的 `_extract_page` 方法中，使用 `classify_llm_error`
增强错误消息，并通过既有的 `progress_callback('page_error', ...)` 上报到 UI。

#### Scenario: paddleocr-vl-0.9b max_tokens 超限

- **WHEN** LLM OCR API 调用抛出 `BadRequestError` 且消息含 `max_tokens`
- **AND** `config.OCR_LLM_MAX_TOKENS` 为默认值 `8000`
- **THEN** 返回给上层的 `error_msg` SHALL 包含 `classify_llm_error` 返回的 `user_message`
- **AND** SHALL 包含当前 `OCR_LLM_MAX_TOKENS` 值
- **AND** SHALL 建议降低 `OCR_LLM_MAX_TOKENS` 环境变量
- **AND** 通过 `progress_callback('page_error', ...)` 传播到 UI

#### Scenario: LLM OCR 认证失败

- **WHEN** LLM OCR API 调用抛出 `AuthenticationError`
- **THEN** `error_msg` SHALL 包含 `API 密钥无效或已过期` 提示
- **AND** 通过 `progress_callback('page_error', ...)` 传播到 UI

### Requirement: 翻译调用点保留异常类型并增强消息

系统 SHALL 在 `silicon_flow_translator.py` / `qianfan_translator.py` / `aiping_translator.py`
的异常处理中，使用 `classify_llm_error` 生成友好消息，并通过 `raise ... from e` 保留原始异常类型，
使顶层 [services/translation_service.py:270](file:///Users/chunju/work/pdfTrans/services/translation_service.py#L270)
能区分错误类型。

#### Scenario: 翻译时 API 密钥无效

- **WHEN** 翻译 API 调用抛出 `AuthenticationError`
- **THEN** 模块 SHALL 重新抛出异常（保留原始类型或通过 `raise ... from e`）
- **AND** 异常消息 SHALL 包含 `classify_llm_error` 返回的友好消息
- **AND** 顶层 `task.set_error` 收到的消息 SHALL 包含 `API 密钥无效` 字样

### Requirement: 静默吞没点增加 UI 上报

系统 SHALL 在以下静默吞没点增加 `task.add_warning(...)` 上报，使 UI 能感知 LLM 调用失败：

#### Scenario: format_blocks 失败上报

- **WHEN** [modules/translator.py:189](file:///Users/chunju/work/pdfTrans/modules/translator.py#L189) `format_blocks` 抛出异常
- **THEN** [services/translation_content.py:155-166](file:///Users/chunju/work/pdfTrans/services/translation_content.py#L155) 调用处 SHALL 调用 `task.add_warning("排版失败，已回退到未排版译文", {"process": "format", "error": friendly_message})`
- **AND** 继续返回未排版译文（保持现有降级行为）

#### Scenario: 表格行翻译失败上报

- **WHEN** [services/translation_table.py:87-119](file:///Users/chunju/work/pdfTrans/services/translation_table.py#L87) 表格行翻译抛出异常
- **THEN** SHALL 调用 `task.add_warning("表格行翻译失败，已回退到原文", {"process": "table_translation", "error": friendly_message})`
- **AND** 继续回退原文（保持现有降级行为）

#### Scenario: 术语提取失败上报

- **WHEN** [services/glossary_service.py:91-96](file:///Users/chunju/work/pdfTrans/services/glossary_service.py#L91) 术语提取抛出异常
- **THEN** SHALL 调用 `task.add_warning("术语提取失败，翻译将不使用术语表", {"process": "glossary", "error": friendly_message})`
- **AND** 继续返回空术语表（保持现有降级行为）

## MODIFIED Requirements

### Requirement: `_extract_page` 异常处理

**原行为**（[modules/ocr/llm_extractor.py:486-489](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_extractor.py#L486)）:
```python
except Exception as e:
    logger.error(f"LLM OCR提取第{page_num}页失败: {e}", exc_info=True)
    error_msg = f"LLM OCR API 请求失败: {str(e)}"
    return (None, error_msg)
```

**新行为**:
```python
from modules.llm_error_handler import classify_llm_error

except Exception as e:
    logger.error(f"LLM OCR提取第{page_num}页失败: {e}", exc_info=True)
    error_info = classify_llm_error(e)
    error_msg = f"LLM OCR API 请求失败: {error_info['user_message']}"
    # max_tokens 超限时追加当前配置值
    if error_info['category'] == 'bad_request_max_tokens':
        error_msg += f"（当前 OCR_LLM_MAX_TOKENS={config.OCR_LLM_MAX_TOKENS}）"
    return (None, error_msg)
```

### Requirement: 翻译模块异常重新抛出

**原行为**（以 [modules/silicon_flow_translator.py:87](file:///Users/chunju/work/pdfTrans/modules/silicon_flow_translator.py#L87) 为例）:
```python
except Exception as e:
    raise Exception(f"硅基流动翻译失败: {str(e)}")
```

**新行为**:
```python
from modules.llm_error_handler import classify_llm_error

except Exception as e:
    error_info = classify_llm_error(e)
    raise Exception(f"硅基流动翻译失败: {error_info['user_message']}") from e
```

## Implementation Notes

- `classify_llm_error` 应设计为纯函数，无副作用，便于测试
- 对于 `BadRequestError` 含 `max_tokens` 的情况，`user_message` 应包含通用建议
  （「请降低 max_tokens 配置」），具体的环境变量名（`OCR_LLM_MAX_TOKENS` vs
  `GLOSSARY_MAX_TOKENS`）由调用点在拼接时附加，因为工具函数无法知道调用上下文
- 翻译模块使用 `raise ... from e` 保留异常链，便于调试时追溯
- 静默吞没点的 `task.add_warning` 应在现有 `logger.error` 之后、返回默认值之前调用
- 语义分析模块（`semantic_analyzer.py` / `aiping_semantic_analyzer.py`）的失败为可选优化
  降级，不影响主流程，仅增强 `logger.error` 内容，不强制要求 UI 上报（避免警告泛滥）
- `markdown_generator.py` 的 `_call_api` 已通过外层 `MarkdownGenerationResult.add_warning`
  上报，仅需增强错误消息内容
- 不修改 `config.py`、`.env.example`、`SKILL.md`
