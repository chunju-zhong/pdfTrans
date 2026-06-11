# 修复 OCR 超时误杀正在处理的任务 Spec

## Why
OCR 处理 40 页 PDF 时，在第 37 页被总时间超限强制终止。`system_profiler.py` 中硬编码了 3600 秒上限，40 页 PDF 在 "low" 分级下实际需要约 7500 秒但被截断到 3600 秒。同时 `config.py` 中的 `OCR_MAX_TOTAL_TIME` 配置项从未被引用，且重试时超时预算不会增加。

## What Changes
- 移除 `system_profiler.py` 中的 3600 秒硬编码上限，改为可配置值
- 让 `config.py` 中的 `OCR_MAX_TOTAL_TIME` 真正生效，作为超时上限的配置入口
- 在 `_run_ocr_once` 中根据实际进度动态延长超时：当 OCR 正常推进时，按已完成页数与已用时间重新估算剩余时间并延长
- 重试时根据降级后的参数适当增加超时预算

## Impact
- Affected code: `modules/ocr/system_profiler.py`、`modules/ocr/ocr_worker.py`、`config.py`

## ADDED Requirements

### Requirement: 动态延长超时
系统 SHALL 在 OCR 子进程正常推进时（收到 step_progress 消息），根据已完成页数和已用时间重新估算剩余时间，动态延长 `max_total_time`，避免正在正常处理的任务被误杀。

#### Scenario: OCR 正常推进但即将超时
- **WHEN** OCR 子进程持续发送心跳和进度消息，但已用时间接近 `max_total_time`
- **THEN** 系统根据已完成页数估算剩余时间，动态延长超时，不终止子进程

#### Scenario: OCR 子进程真正死机
- **WHEN** OCR 子进程心跳中断超过 `heartbeat_timeout`
- **THEN** 系统判定子进程死机，终止子进程

### Requirement: 重试时增加超时预算
系统 SHALL 在 OCR 重试时适当增加超时预算，避免降级后因同样的超时限制再次失败。

#### Scenario: OCR 超时后重试
- **WHEN** OCR 因总时间超限触发重试
- **THEN** 重试时 `max_total_time` 增加 50%

## MODIFIED Requirements

### Requirement: 超时上限可配置
将 `system_profiler.py` 中的 3600 秒硬编码上限改为从 `config.OCR_MAX_TOTAL_TIME` 读取，使超时上限可通过配置文件调整。`compute_timeout_params` 计算出的 `max_total_time` 不再被硬编码值截断。

### Requirement: config.py 中 OCR_MAX_TOTAL_TIME 生效
`config.py` 中的 `OCR_MAX_TOTAL_TIME` 作为动态参数计算结果的上限（cap），在 `run_ocr_in_subprocess` 中生效。当动态计算的超时值超过此上限时，使用此上限值。
