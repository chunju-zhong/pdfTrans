# 修复语义分析器 JSON 代码栅栏解析失败 Spec

## Why

`AipingSemanticAnalyzer` 与基类 `SemanticAnalyzer` 在解析 LLM 返回的合并决策时，直接调用 `json.loads(analysis_result)`，未剥离 Markdown 代码栅栏（```` ```json ... ``` ````）。当 LLM 尽管被提示词要求"不要包含 Markdown 代码块标记"，仍将 JSON 包裹在 ```` ```json ```` 栅栏中返回时（这是许多模型的常见行为），`json.loads` 抛出 `JSONDecodeError`，触发最多 3 次重试。若 LLM 一致地包裹栅栏，3 次重试全部失败，最终回退到默认值（单次返回 `False`，批量返回全 `False` 列表），导致语义合并完全失效，进而损害译文段落的连续性。

错误日志证据：
```
2026-06-27 09:25:34,159 - modules.aiping_semantic_analyzer - ERROR - 无法解析的原始结果: '```json
{"merge": [true, false, ...]}
```'
```

原始结果以 ```` ```json ```` 开头、以 ```` ``` ```` 结尾，`json.loads` 无法解析。

## What Changes

- 在基类 `SemanticAnalyzer` 中新增 `_extract_json_from_response(text)` 辅助方法，三级容错提取 JSON（与 `modules/ocr/llm_response_parser.py:LlmOcrResponseParser._extract_json` 同构）：
  1. 文本 strip 后以 `{` 开头时直接 `json.loads`
  2. 用正则 `r'```(?:json)?\s*(.*?)\s*```'`（DOTALL）从代码栅栏中提取并 `json.loads`
  3. 回退：取第一个 `{` 到最后一个 `}` 之间的子串 `json.loads`
  4. 全部失败时返回 `None`
- `SemanticAnalyzer.analyze_semantic_relationship`（非流式单次）：将 `json.loads(analysis_result)` 替换为 `_extract_json_from_response` 调用，返回 `None` 时走原有异常分支
- `SemanticAnalyzer.batch_analyze_semantic_relationship`（非流式批量）：同上替换
- `AipingSemanticAnalyzer.analyze_semantic_relationship`（流式单次）：同上替换
- `AipingSemanticAnalyzer.batch_analyze_semantic_relationship`（流式批量）：同上替换
- 保持原有的重试与默认值回退逻辑不变；仅改变 JSON 解析的预处理步骤

## Impact

- Affected specs: 无（独立修复）
- Affected code:
  - `modules/semantic_analyzer.py` — 新增 `_extract_json_from_response` 方法；修改 `analyze_semantic_relationship` 和 `batch_analyze_semantic_relationship` 的 JSON 解析处
  - `modules/aiping_semantic_analyzer.py` — 修改 `analyze_semantic_relationship` 和 `batch_analyze_semantic_relationship` 的 JSON 解析处（继承基类新方法）

## ADDED Requirements

### Requirement: 语义分析器 JSON 响应容错解析

系统 SHALL 在解析 LLM 返回的语义分析结果时，剥离 Markdown 代码栅栏并容错提取 JSON。

#### Scenario: LLM 返回纯 JSON（无栅栏）
- **WHEN** LLM 返回内容 strip 后以 `{` 开头
- **THEN** SHALL 直接 `json.loads` 解析

#### Scenario: LLM 返回 ```json 代码栅栏包裹的 JSON
- **WHEN** LLM 返回内容包含 ```` ```json ... ``` ```` 或 ```` ``` ... ``` ```` 代码栅栏
- **THEN** SHALL 用正则提取栅栏内内容并 `json.loads` 解析
- **AND** SHALL 不触发重试

#### Scenario: LLM 返回包含 JSON 的混合文本
- **WHEN** LLM 返回内容既非纯 JSON 也非标准代码栅栏，但包含 `{` 和 `}`
- **THEN** SHALL 取第一个 `{` 到最后一个 `}` 之间的子串尝试 `json.loads`

#### Scenario: 三级容错全部失败
- **WHEN** 三级提取策略均无法得到有效 JSON
- **THEN** SHALL 返回 `None`
- **AND** 调用方 SHALL 按原有逻辑触发重试或返回默认值

## MODIFIED Requirements

### Requirement: 单次语义分析响应解析

`SemanticAnalyzer.analyze_semantic_relationship` 与 `AipingSemanticAnalyzer.analyze_semantic_relationship` SHALL 使用 `_extract_json_from_response` 预处理 LLM 原始响应后再解析。

#### Scenario: 提取成功
- **WHEN** `_extract_json_from_response` 返回有效字典
- **THEN** SHALL 从字典读取 `merge` 字段并转为布尔值返回

#### Scenario: 提取返回 None
- **WHEN** `_extract_json_from_response` 返回 `None`
- **THEN** SHALL 视为解析失败，按原有重试/默认值逻辑处理（不抛出未捕获异常）

### Requirement: 批量语义分析响应解析

`SemanticAnalyzer.batch_analyze_semantic_relationship` 与 `AipingSemanticAnalyzer.batch_analyze_semantic_relationship` SHALL 使用 `_extract_json_from_response` 预处理 LLM 原始响应后再解析。

#### Scenario: 提取成功且 merge 数组长度匹配
- **WHEN** `_extract_json_from_response` 返回有效字典且 `merge` 数组长度等于 `len(blocks) - 1`
- **THEN** SHALL 将数组元素转为布尔值列表返回

#### Scenario: 提取返回 None
- **WHEN** `_extract_json_from_response` 返回 `None`
- **THEN** SHALL 视为解析失败，按原有重试/默认值列表逻辑处理
