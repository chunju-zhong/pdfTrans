# OCR 提取管线重构：分步版面分析避免内存超限 Spec

## Why
步骤1创建管线时 `use_formula=True` 会同时加载公式检测+识别模型，导致步骤1内存峰值增加 300-500MB。在内存紧张的环境下（<8GB），这可能导致 swap 颠簸和心跳中断。当前架构中公式模型被冗余加载（步骤1检测 + 步骤3识别），且步骤2/3逐页管线每次都重新加载版面+OCR基础模型。

## What Changes
- 步骤1改为 `use_formula=False`，仅做版面分析+文本OCR，不加载公式模型
- 新增步骤1.5：纯公式版面分析，使用轻量管线（`use_formula=True, use_table=False`）逐页检测公式区域
- 步骤3公式识别不再依赖步骤1的 `has_formula`，改用步骤1.5的检测结果
- 步骤1.5采用逐页管线模式，降低内存峰值
- 公式识别被跳过时通过 status_callback 通知用户
- 检查各步骤管线释放是否完整，确保内存及时回收

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`
- Affected specs: fix-step1-formula-detection（步骤1 use_formula 参数变更）

## ADDED Requirements

### Requirement: 步骤1仅做版面分析+文本OCR
步骤1创建管线时 `use_formula=False`，不加载公式模型，降低内存峰值约 300-500MB。

#### Scenario: 步骤1内存降低
- **WHEN** 步骤1以 `use_formula=False` 创建管线
- **THEN** 版面分析模型检测到 text/table/image 区域，但不会输出 formula 标签
- **AND** 步骤1内存峰值比 `use_formula=True` 时降低约 300-500MB

#### Scenario: 步骤1仍能检测表格
- **WHEN** 步骤1以 `use_formula=False` 创建管线
- **THEN** 版面分析模型仍能输出 `table` 标签（与 use_formula 无关），`has_table` 正确设置

### Requirement: 新增步骤1.5纯公式版面分析
在步骤1完成后、步骤2之前，新增步骤1.5：逐页创建公式管线检测公式区域。

#### Scenario: 步骤1.5逐页检测公式
- **WHEN** 步骤1完成，进入步骤1.5
- **THEN** 对每个目标页面，创建 `use_formula=True` 管线，运行 `pipeline.predict()`，检查 `parsing_res_list` 中是否有 `formula`/`formula_number` 标签
- **AND** 检测完一页后立即销毁管线 + `gc.collect()`
- **AND** 设置 `has_formula=True/False` 到 `all_layout_results` 中

#### Scenario: 步骤1.5内存可控
- **WHEN** 步骤1.5逐页处理公式检测
- **THEN** 每次只有一页的公式管线在内存中，峰值约 1400-1600MB
- **AND** 处理完一页后管线被销毁，内存回落

#### Scenario: 步骤1.5可用内存不足时跳过并通知用户
- **WHEN** 步骤1.5开始前检查可用内存 < 1.5GB
- **THEN** 跳过步骤1.5，所有页面的 `has_formula` 保持 `False`，步骤3不执行
- **AND** 通过 status_callback 发送警告消息，提示用户公式识别因内存不足被跳过

### Requirement: 公式识别被跳过时通知用户
当公式识别因任何原因被跳过时（内存不足、OCR_SKIP_FORMULA 配置等），系统 SHALL 通过 status_callback 通知用户。

#### Scenario: 内存不足跳过公式识别
- **WHEN** 步骤1.5因可用内存 < 1.5GB 被跳过
- **THEN** 日志记录警告，且进度消息中提示"公式识别因内存不足被跳过"

#### Scenario: 配置跳过公式识别
- **WHEN** `OCR_SKIP_FORMULA=True` 配置跳过公式识别
- **THEN** 进度消息中提示"公式识别已被配置跳过"

### Requirement: 各步骤管线正确释放
每个步骤完成后 SHALL 确保管线对象被完全释放，内存及时回收。

#### Scenario: 步骤1管线释放
- **WHEN** 步骤1完成所有页面的版面分析
- **THEN** `del layout_pipeline` + `gc.collect()` 被调用，内存日志确认释放

#### Scenario: 步骤1.5管线释放
- **WHEN** 步骤1.5每页公式检测完成
- **THEN** `del pipeline` + `gc.collect()` 被调用

#### Scenario: 步骤2管线释放
- **WHEN** 步骤2每页表格识别完成
- **THEN** `del table_pipeline` + `gc.collect()` 被调用

#### Scenario: 步骤3管线释放
- **WHEN** 步骤3每页公式识别完成
- **THEN** `del formula_pipeline` + `gc.collect()` 被调用

### Requirement: 步骤3使用步骤1.5的检测结果
步骤3公式识别根据步骤1.5设置的 `has_formula` 筛选页面，不再依赖步骤1的版面分析结果。

#### Scenario: 步骤3正确触发
- **WHEN** 步骤1.5检测到某页有公式区域
- **THEN** 步骤3对该页执行公式识别，提取 LaTeX 字符串

#### Scenario: 步骤3不执行
- **WHEN** 步骤1.5未检测到任何页面有公式区域（或步骤1.5被跳过）
- **THEN** 步骤3跳过，不加载公式识别管线

## MODIFIED Requirements

### Requirement: 步骤1管线创建参数
`_create_pipeline(use_table=False, use_formula=False, use_region_detection=False)` — 将 `use_formula` 从 `True` 改回 `False`。

## REMOVED Requirements

### Requirement: 步骤1版面分析启用公式检测
**Reason**: 步骤1启用公式检测会导致内存峰值过高，改为步骤1.5独立检测。
**Migration**: 步骤1.5以逐页模式检测公式区域，内存更可控。公式识别被跳过时通知用户。
