# OCR 三层防护 + 分批处理 Spec

## Why
当前 OCR 超时机制只有两层（heartbeat_timeout + max_total_time），无法区分"慢但有进度"和"卡死无进度"的场景，导致大文件（如 800 页 PDF）被误杀。同时没有分批处理机制，所有页面必须在一个子进程中顺序处理，无法分而治之。

## What Changes
- 新增停滞检测（stall detection）：超过 30 分钟无进度则终止，替代 max_total_time 作为主要保护
- 放宽 max_total_time 到 24 小时，仅作为兜底安全网
- 实现分批 OCR 处理：将大 PDF 按批次（每批默认 5 页，可配置）分割，每批独立 OCR，最后合并结果
- 降级超时预算不再被 config_max_total_time 截断

## Impact
- Affected code: `modules/ocr/ocr_worker.py`、`modules/ocr/paddle_extractor.py`、`modules/pdf_extractor.py`、`config.py`

## ADDED Requirements

### Requirement: 停滞检测
系统 SHALL 在 OCR 子进程运行期间检测进度停滞。如果超过 stall_timeout（默认 1800 秒/30 分钟）没有收到 STEP_PROGRESS 消息（即 pages_done 没有增加），判定为停滞并终止子进程。

#### Scenario: OCR 正常推进大文件
- **WHEN** OCR 子进程持续发送进度消息（pages_done 持续增加）
- **THEN** 停滞检测不触发，OCR 继续运行，不受 max_total_time 限制（动态延长机制生效）

#### Scenario: OCR 卡在某一页无进度
- **WHEN** OCR 子进程超过 30 分钟没有发送 STEP_PROGRESS 消息
- **THEN** 停滞检测触发，终止子进程，抛出 OcrRetryableError

#### Scenario: OCR 进程死亡
- **WHEN** OCR 子进程崩溃或完全冻结
- **THEN** heartbeat_timeout（90-360 秒）触发，终止子进程

### Requirement: 分批 OCR 处理
系统 SHALL 将大 PDF 按批次分割处理。当 PDF 页数超过 batch_size（默认 5 页，可通过 OCR_BATCH_SIZE 环境变量配置）时，将页面分成多批，每批独立在子进程中 OCR，最后合并结果。

#### Scenario: 800 页 PDF 处理
- **WHEN** 用户上传 800 页 PDF
- **THEN** 系统将其分为 160 批（每批 5 页），每批独立 OCR，最后合并为完整的提取结果

#### Scenario: 40 页 PDF 处理
- **WHEN** 用户上传 40 页 PDF（超过 batch_size）
- **THEN** 系统将其分为 8 批（每批 5 页），分批处理

#### Scenario: 某批处理失败
- **WHEN** 某批 OCR 处理失败（超时、崩溃等）
- **THEN** 该批重试（遵循现有重试机制），不影响其他批次

## MODIFIED Requirements

### Requirement: max_total_time 作为兜底安全网
将 `OCR_MAX_TOTAL_TIME` 从 7200 秒（2 小时）放宽到 86400 秒（24 小时），仅作为极端情况的兜底安全网，不再作为主要保护机制。

### Requirement: 降级超时预算不被截断
降级后计算出的 `max_total_time` 不再被 `config_max_total_time` 截断，允许降级后获得更长的超时预算。
