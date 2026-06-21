# 修复LLM OCR `_extract_json` 误判导致页面无翻译内容 Spec

## Why

第51页（以及第130、153、236、262页）在翻译输出中完全没有翻译内容。通过深入分析日志发现，根因不是页眉页脚误判，而是 LLM OCR 提取阶段这些页面就产出了0个文本块。

**关键日志证据**：
- `第 51 页提取统计: 总块数=0, 正文块=0, 非正文块=0` — 提取阶段就没有文本块
- 第51页有 LLM OCR 原始响应，但**没有** `"使用<|ref|>标签格式解析"` 日志
- 相邻的第50页和第52页都有正常的格式解析日志和解析结果日志
- 没有任何 ERROR 或 WARNING 日志

**根因**：运行时版本（git HEAD）的 `_extract_json` 有第3级容错（`text.find('{')` + `text.rfind('}')`），当 LLM OCR 响应中包含代码内容（如 Python 字典 `{"question": query}`）时，可能将代码中的花括号之间的内容误判为 JSON。`_parse_json_response` 被调用后，因为解析出的 JSON 不包含 `text_blocks` 键，返回空列表 `([], [], [])`。由于空元组在 Python 中是 truthy 的，调用方不会添加空页面警告，而是直接添加了0个文本块的页面。

## What Changes

- **修复 `_extract_json` 的第3级容错**：当响应包含 `<|ref|>` 标签时，不应尝试 JSON 提取，因为 `<|ref|>` 标签格式是 DeepSeek-OCR 的原生格式
- **在 `_parse_response` 中调整格式检测优先级**：当响应包含 `<|ref|>` 标签时，优先使用 `<|ref|>` 标签格式解析，而非 JSON 格式
- **增加诊断日志**：在 `_parse_json_response` 被调用时记录格式解析日志，便于排查
- **修复空结果处理**：当 `_parse_json_response` 返回空列表时，应继续尝试其他格式而非直接返回

## Impact

- Affected code: `modules/ocr/llm_extractor.py` 的 `_parse_response` 和 `_extract_json` 函数
- 行为变更：包含 `<|ref|>` 标签的响应将优先使用标签格式解析，避免被 JSON 容错逻辑误判

## 根因分析

### 根因（已确认）：`_extract_json` 第3级容错误判导致 `<|ref|>` 标签格式响应被跳过

**代码证据**（git HEAD 版本 `llm_extractor.py`）：

1. `_parse_response` 的格式检测优先级：JSON > `<|ref|>` > Markdown
2. `_extract_json` 第3级容错：`text.find('{')` + `text.rfind('}')` + `json.loads(text[start:end+1])`
3. 第51页的 LLM OCR 响应包含代码内容（Python 代码示例），代码中可能包含合法的 JSON 片段

**日志证据**：

| 页面 | 原始响应 | `<|ref|>` 格式解析日志 | 解析结果日志 | 提取统计 |
|------|----------|------------------------|-------------|---------|
| 第50页 | 有 | 有 | 16个文本块 | 16正文/0非正文 |
| **第51页** | 有 | **无** | **无** | **0/0** |
| 第52页 | 有 | 有 | 13个文本块 | 16正文/0非正文 |

第51页没有格式解析日志，说明没有进入 `<|ref|>` 标签路径。唯一可能是在 JSON 路径被 `_extract_json` 误判后走了 `_parse_json_response`，而 `_parse_json_response` 没有格式解析日志。

**受影响页面**：第51、130、153、236、262页（共5页，均为包含代码内容的页面）

### 当前工作区代码已修复优先级

当前工作区的 `llm_extractor.py` 已将格式检测优先级改为 `<|ref|>` > JSON > Markdown，这正确地避免了误判。但 `_extract_json` 的第3级容错仍然存在，可能在其他场景下导致问题。

## ADDED Requirements

### Requirement: `_parse_response` 中 `<|ref|>` 标签格式优先于 JSON

系统 SHALL 在 `_parse_response` 中，当响应包含 `<|ref|>` 和 `<|/ref|>` 标签时，优先使用 `<|ref|>` 标签格式解析，不尝试 JSON 提取。

#### Scenario: 响应包含 `<|ref|>` 标签和花括号
- **WHEN** LLM OCR 响应同时包含 `<|ref|>` 标签和 `{` / `}` 字符
- **THEN** 系统应使用 `<|ref|>` 标签格式解析，不尝试 JSON 提取
- **AND** 记录 `"使用<|ref|>标签格式解析"` 日志

#### Scenario: 响应只包含 JSON 格式
- **WHEN** LLM OCR 响应不包含 `<|ref|>` 标签，但包含合法 JSON
- **THEN** 系统应使用 JSON 格式解析
- **AND** 记录 `"使用JSON格式解析"` 日志

### Requirement: `_extract_json` 移除第3级容错

系统 SHALL 移除 `_extract_json` 的第3级容错（花括号查找），因为该容错机制过于宽松，容易将代码内容误判为 JSON。

#### Scenario: 响应包含代码中的花括号
- **WHEN** LLM OCR 响应包含代码内容（如 Python 字典），其中包含 `{` 和 `}` 字符
- **THEN** `_extract_json` 不应将花括号之间的内容尝试解析为 JSON

#### Scenario: 响应包含合法 JSON
- **WHEN** LLM OCR 响应以 `{` 开头或被 ```json``` 包裹
- **THEN** `_extract_json` 应正常解析（第1级和第2级容错不受影响）

### Requirement: `_parse_json_response` 增加格式解析日志

系统 SHALL 在 `_parse_json_response` 被调用时记录格式解析日志，便于排查 JSON 误判问题。

#### Scenario: JSON 格式解析被调用
- **WHEN** `_parse_json_response` 被调用
- **THEN** 系统应记录 `"第{page_num}页LLM OCR使用JSON格式解析"` 日志

### Requirement: 空解析结果时尝试回退格式

系统 SHALL 在 `_parse_json_response` 返回空结果时，继续尝试 `<|ref|>` 标签格式和 Markdown 格式解析，而非直接返回空结果。

#### Scenario: JSON 解析返回空结果但响应包含 `<|ref|>` 标签
- **WHEN** `_parse_json_response` 返回空文本块列表，且响应包含 `<|ref|>` 标签
- **THEN** 系统应回退到 `<|ref|>` 标签格式解析

#### Scenario: JSON 解析返回非空结果
- **WHEN** `_parse_json_response` 返回非空文本块列表
- **THEN** 系统应直接返回 JSON 解析结果，不尝试回退

## MODIFIED Requirements

（无修改的已有需求）

## REMOVED Requirements

（无移除的需求）
