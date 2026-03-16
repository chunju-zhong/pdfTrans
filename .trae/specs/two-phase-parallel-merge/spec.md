# 批量语义合并多线程并行化开发方案

## Why
当前批量语义合并采用顺序执行模式，每批10对文本需要串行等待API调用完成。当文本块数量较多时，整体处理时间过长，影响用户体验。需要通过多线程并行化来提升性能。

## What Changes
- 在 `utils/text_processing.py` 中新增两阶段合并方法 `merge_semantic_blocks_with_llm_two_phase`
- 新增并行批量分析方法 `parallel_batch_analyze`，使用 `ThreadPoolExecutor` 并行调用语义分析API
- 保持原有 `merge_semantic_blocks_with_llm` 方法不变，作为兼容备用
- 性能目标：3-5倍提升

## Impact
- Affected specs: 语义合并功能
- Affected code: 
  - `utils/text_processing.py` - 核心合并逻辑
  - `services/translation_service.py` - 调用入口（可能需要修改配置开关）

## ADDED Requirements

### Requirement: 两阶段并行合并
系统 SHALL 提供两阶段并行合并功能：
1. 阶段1：并行调用LLM获取所有文本对的合并判断
2. 阶段2：根据预存的判断结果顺序执行合并

#### Scenario: 两阶段合并正常执行
- **GIVEN** 有100个文本块需要合并
- **WHEN** 调用 `merge_semantic_blocks_with_llm_two_phase` 方法
- **THEN** 
  - 系统并行调用API获取所有合并判断（约5-10个批次）
  - 系统顺序处理所有判断结果，生成合并块
  - 合并结果与原串行逻辑完全一致

### Requirement: 并行度可控
系统 SHALL 提供并行度配置能力：
- 最大并行线程数可配置（建议默认3-5）
- 批次大小可配置（建议默认20对）

#### Scenario: 并行度配置
- **GIVEN** 用户配置 max_workers=3, batch_size=20
- **WHEN** 处理1000对文本
- **THEN** 系统使用3个线程并行执行，每批20对

### Requirement: 错误处理
系统 SHALL 处理API调用失败的情况：
- 单个批次API调用失败时，应有重试机制
- 重试失败后，记录日志并使用默认值（不合并）

#### Scenario: API调用失败重试
- **GIVEN** 某批次API调用失败
- **WHEN** 调用合并方法
- **THEN** 系统自动重试最多3次，重试失败后使用默认值

## MODIFIED Requirements

### Requirement: 翻译服务集成
修改 `translation_service.py` 中的语义合并调用逻辑，支持通过配置切换使用两阶段并行方法。

#### Scenario: 启用两阶段合并
- **GIVEN** 配置项 `use_two_phase_merge=True`
- **WHEN** 调用翻译服务处理PDF
- **THEN** 使用两阶段并行合并方法处理语义合并

## REMOVED Requirements

### Requirement: 无
当前不涉及功能移除。

