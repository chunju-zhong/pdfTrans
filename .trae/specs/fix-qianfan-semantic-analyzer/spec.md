# 修复百度千帆语义分析器缺失分支 Spec

## Why

`services/translation_service.py` 的 `get_semantic_analyzer()` 方法缺失了 `qianfan` 分支，导致选择百度千帆翻译引擎时在创建语义分析器阶段抛出 `ValueError("无效的语义分析器类型")`。

此前该问题被 `process_translation` 中 `translation_model` 未定义导致的 `NameError` 掩盖（该 NameError 在 `_create_translators` 调用之前就已抛出）。修复 `NameError` 后，代码到达 `get_semantic_analyzer` 并触发此缺陷。

`SemanticAnalyzerFactory.create_analyzer` 已支持 `qianfan` 类型（复用标准 `SemanticAnalyzer` 基类），仅 `translation_service.py` 的分派层缺失对应分支。

## What Changes

- `services/translation_service.py` `get_semantic_analyzer` 方法：新增 `elif analyzer_type == 'qianfan'` 分支，读取 `config.QIANFAN_API_KEY/URL/MODEL`，通过 `SemanticAnalyzerFactory.create_analyzer('qianfan', ...)` 创建标准语义分析器

## Impact

- Affected specs: 百度千帆语义分析器分派
- Affected code:
  - `services/translation_service.py` — `get_semantic_analyzer()` 新增 `qianfan` 分支

## ADDED Requirements

### Requirement: 百度千帆语义分析器分派

系统 SHALL 在 `get_semantic_analyzer('qianfan')` 调用时返回标准 `SemanticAnalyzer` 实例。

#### Scenario: 创建 qianfan 语义分析器
- **WHEN** `get_semantic_analyzer('qianfan')` 被调用
- **THEN** SHALL 检查 `config.QIANFAN_API_KEY` 是否已配置，未配置时抛出 `ValueError("百度千帆语义分析API配置不完整")`
- **AND** SHALL 通过 `SemanticAnalyzerFactory.create_analyzer('qianfan', config.QIANFAN_API_KEY, config.QIANFAN_API_URL, model or config.QIANFAN_MODEL)` 创建实例
- **AND** SHALL 返回 `SemanticAnalyzer` 实例
