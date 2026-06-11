# 优化提取进度与提示信息 Spec

## Why
当前进度系统存在多个问题：阶段百分比分配不合理（OCR 提取是最耗时的步骤却只占 25%）、进度提示与实际操作不符（文件生成完毕后仍显示"正在生成输出文件"）、无表格时进度跳跃、整数截断导致小范围阶段进度不动、语义合并和生成阶段无细粒度进度。用户看到的进度条经常卡住或与实际状态脱节。

## What Changes
- 重新分配阶段百分比区间，让耗时长的阶段占据更大比例
- 修复 `_complete_task` 中进度提示与实际操作不符的问题
- 无表格时平滑过渡，不跳跃
- 修复整数截断问题，使用四舍五入替代截断
- 为语义合并和生成阶段添加细粒度进度
- 错误时保留当前进度而非归零

## Impact
- Affected code: `models/phase_config.py`、`models/task.py`、`services/translation_service.py`
- Affected specs: add-ocr-progress-feedback（OCR 进度回调逻辑不变，但 extraction 阶段区间改变）

## ADDED Requirements

### Requirement: 重新分配阶段百分比区间
系统 SHALL 根据各阶段实际耗时占比重新分配百分比区间，使进度条推进更符合用户感知。

新分配方案：
| 阶段 | 名称 | 旧区间 | 新区间 | 理由 |
|------|------|--------|--------|------|
| init | 初始化 | 0-10% | 0-5% | 初始化很快 |
| extraction | 文本图表提取 | 10-35% | 5-40% | OCR 提取是最耗时步骤 |
| semantic_merge | 语义合并 | 35-40% | 40-50% | LLM 合并可耗时较长 |
| translation | 文本翻译 | 40-80% | 50-85% | 主要翻译阶段 |
| table_translation | 表格翻译 | 80-90% | 85-92% | 表格翻译 |
| generation | 生成输出 | 90-95% | 92-98% | 文件生成 |
| clean | 清理临时文件 | 95-100% | 98-100% | 清理很快 |

#### Scenario: OCR 模式下进度推进更平滑
- **WHEN** 用户使用 OCR 模式翻译一个 100 页 PDF
- **THEN** 提取阶段占据 5%-40% 的进度区间，进度条在 OCR 期间持续平滑推进

#### Scenario: 非 OCR 模式下进度推进正常
- **WHEN** 用户使用普通模式翻译 PDF
- **THEN** 提取阶段快速完成，进度条迅速进入翻译阶段

### Requirement: 修复进度提示与实际操作不符
系统 SHALL 确保进度提示消息与当前实际操作一致。

#### Scenario: 文件生成完毕后不再显示"正在生成输出文件"
- **WHEN** `_generate_outputs` 完成后进入 `_complete_task`
- **THEN** 进度消息显示"正在清理临时文件..."而非"正在生成输出文件..."

#### Scenario: 清理完成后显示完成消息
- **WHEN** 临时文件清理完成
- **THEN** 进度消息显示"翻译完成！"

### Requirement: 无表格时平滑过渡
系统 SHALL 在无表格时跳过 table_translation 阶段，进度从 translation 阶段平滑过渡到 generation 阶段。

#### Scenario: PDF 无表格
- **WHEN** 提取结果中没有表格
- **THEN** 进度从 translation 阶段结束后直接进入 generation 阶段，不出现跳跃

### Requirement: 修复整数截断问题
系统 SHALL 使用四舍五入替代整数截断来计算进度百分比，避免小范围阶段进度不动。

#### Scenario: 语义合并阶段进度推进
- **WHEN** 语义合并阶段（40-50%，10% 范围）内部进度为 10%
- **THEN** 整体进度为 41%（40 + 10 * 10 / 100 = 41），而非被截断为 40%

### Requirement: 语义合并阶段细粒度进度
系统 SHALL 在语义合并阶段提供细粒度进度更新，而非仅 0% 和 100% 两个状态。

#### Scenario: 规则合并进度
- **WHEN** 使用规则方法合并语义块，处理到一半
- **THEN** 进度消息显示"正在合并语义块: X/Y"

#### Scenario: LLM 合并进度
- **WHEN** 使用 LLM 方法合并语义块，处理到一半
- **THEN** 进度消息显示"正在合并语义块: X/Y"

### Requirement: 生成阶段细粒度进度
系统 SHALL 在生成输出文件时提供细粒度进度更新。

#### Scenario: 多格式输出进度
- **WHEN** 同时生成 PDF 和 DOCX 输出
- **THEN** 进度消息显示"正在生成输出文件: PDF..."和"正在生成输出文件: DOCX..."

### Requirement: 错误时保留当前进度
系统 SHALL 在任务出错时保留当前进度值，而非归零。

#### Scenario: 翻译过程中出错
- **WHEN** 翻译进行到 60% 时发生错误
- **THEN** 进度条保持在 60%，状态变为 error，消息显示错误信息

## MODIFIED Requirements

### Requirement: calculate_progress 使用四舍五入
`calculate_progress` 函数 SHALL 使用 `round()` 替代 `//` 整数除法来计算进度百分比。

### Requirement: update_phase_progress 使用四舍五入
`Task.update_phase_progress` 方法 SHALL 使用 `round()` 替代 `//` 整数除法来计算整体进度。

### Requirement: set_error 保留当前进度
`Task.set_error` 方法 SHALL 保留当前 `self.progress` 值，不将其归零。

### Requirement: _complete_task 修正进度流程
`_complete_task` 方法 SHALL 按以下顺序更新进度：
1. `generation` 50% → "正在生成输出文件..."（在 `_generate_outputs` 之前调用）
2. `generation` 100% → "输出文件生成完成"（在 `_generate_outputs` 之后调用）
3. `clean` 0% → "正在清理临时文件..."
4. `clean` 100% → "翻译完成！"

当前错误流程：先设置 generation 50%（但文件已生成完毕），再设 clean 0%，再设 generation 100%。

### Requirement: translate_tables 无表格时跳过
`translate_tables` 方法 SHALL 在无表格时直接返回空列表，不更新 table_translation 阶段进度，使进度自然从 translation 阶段过渡到 generation 阶段。
