# 移除步骤1.5 + 换用小模型 + 移除超时限制 Spec

## Why

公式识别在 macOS 纯 CPU 推理下极慢（PP-FormulaNet_plus-M 模型计算量大），推理期间持有 GIL 导致心跳线程无法运行，外层监控判定进程死机并杀掉。换用更轻量的 PP-FormulaNet_plus-S 小模型可以显著缩短推理时间，同时移除步骤1.5（冗余）和所有超时限制，让公式识别跑到底看最终能否完成。

## What Changes

- **移除步骤1.5**：步骤1已能检测公式区域，步骤1.5完全冗余
- **换用 PP-FormulaNet_plus-S 小模型**：推理速度更快，减少卡死概率
- **移除步骤3的 ThreadPoolExecutor 超时**：已被证明在 GIL 被持有时无效，改为直接调用 `pipeline.predict()`
- **禁用心跳超时**：将 `OCR_HEARTBEAT_TIMEOUT` 默认值设为 `0`（表示禁用），心跳超时检查逻辑中当值为0时跳过，让公式识别跑到底
- **增加诊断日志**：记录公式识别实际耗时，帮助判断是"极慢"还是"卡死"

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`、`modules/ocr/ocr_worker.py`、`config.py`
- Affected specs: `fix-batch-formula-memory-leak`、`fix-formula-predict-gil-hang`

## ADDED Requirements

### Requirement: 移除步骤1.5

系统 SHALL 移除步骤1.5（公式版面分析）。步骤1（`use_formula=False`）的版面分析模型已能检测公式区域并设置 `has_formula=True`，步骤1.5 完全冗余。

#### Scenario: 含公式页面的公式检测

- **WHEN** 步骤1处理含公式的页面
- **THEN** 版面分析模型检测到 `formula`/`formula_number` 标签
- **AND** `has_formula=True` 被正确设置
- **AND** 步骤3正常触发公式识别

### Requirement: 换用 PP-FormulaNet_plus-S 小模型

系统 SHALL 将公式识别模型从默认的 PP-FormulaNet_plus-M 切换为 PP-FormulaNet_plus-S。S 模型更轻量，推理速度更快。

#### Scenario: 创建公式识别管线

- **WHEN** 步骤3创建 `use_formula=True` 的管线
- **THEN** 传入 `formula_recognition_model_name="PP-FormulaNet_plus-S"` 参数
- **AND** 使用小模型进行公式识别

### Requirement: 移除步骤3的 ThreadPoolExecutor 超时

系统 SHALL 移除步骤3中的 ThreadPoolExecutor 超时机制。该机制在 C++ 推理持有 GIL 时完全无效（超时后无法获取 GIL 处理异常）。改为直接调用 `pipeline.predict()`。

#### Scenario: 公式识别直接调用

- **WHEN** 步骤3对某页执行公式识别
- **THEN** 直接调用 `pipeline.predict(img_array)`，不使用 ThreadPoolExecutor 包装
- **AND** 记录 predict 开始时间和结束时间

### Requirement: 禁用心跳超时

系统 SHALL 将 `OCR_HEARTBEAT_TIMEOUT` 默认值设为 `0`（表示禁用）。当 `heartbeat_timeout` 为 `0` 时，心跳超时检查逻辑跳过，不再因心跳中断杀掉进程。公式识别推理期间 GIL 被持有导致心跳暂停是预期行为，不应触发进程终止。

#### Scenario: 心跳超时配置为0

- **WHEN** `OCR_HEARTBEAT_TIMEOUT` 配置为 `0`
- **THEN** 心跳超时检查被跳过
- **AND** 即使心跳中断也不会杀掉 OCR 子进程
- **AND** OCR 子进程可以运行到自然完成

#### Scenario: 心跳超时配置为非0值

- **WHEN** `OCR_HEARTBEAT_TIMEOUT` 配置为非0正整数
- **THEN** 心跳超时检查正常执行（保持原有行为）
- **AND** 心跳中断超过阈值时仍会杀掉进程

### Requirement: 增加诊断日志

系统 SHALL 在步骤3中添加诊断日志，记录公式识别的实际执行时间，帮助判断是"极慢"还是"卡死"。

#### Scenario: 公式识别完成

- **WHEN** 步骤3某页公式识别完成
- **THEN** 日志记录 "步骤3第N页公式识别完成，耗时XXX秒"

#### Scenario: 步骤1完成后记录公式检测信息

- **WHEN** 步骤1完成
- **THEN** 日志记录哪些页面检测到公式

## MODIFIED Requirements

### Requirement: 步骤1.5 公式版面分析

步骤1.5 被完全移除。步骤1的版面分析模型已能检测公式区域。

### Requirement: 步骤3 超时处理逻辑

步骤3不再使用 ThreadPoolExecutor 超时机制。改为直接调用 `pipeline.predict()`，不再设置任何超时。

### Requirement: 心跳超时配置

`OCR_HEARTBEAT_TIMEOUT` 默认值改为 `0`（禁用）。用户可通过环境变量设置为非0值来恢复心跳超时检查。

## REMOVED Requirements

### Requirement: 步骤1.5 纯公式版面分析

**Reason**: 步骤1（`use_formula=False`）的版面分析模型已能检测公式区域，步骤1.5完全冗余。
**Migration**: 步骤1检测到的公式区域直接传递给步骤3进行公式识别。
