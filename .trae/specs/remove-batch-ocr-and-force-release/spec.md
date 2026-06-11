# 移除分批识别与强制释放功能 Spec

## Why
根据最新日志验证，分批识别（batch OCR）和强制释放内存（`_force_release_memory` / `malloc_trim`）两项功能均无实际效果。C++ 底层（PaddlePaddle 内存池）不会因 `malloc_trim` 或 `malloc_zone_pressure_relief` 而释放内存，分批处理也无法降低单进程内存峰值（每批仍需加载完整模型）。这两项功能增加了代码复杂度、日志噪音和批次间等待时间，应当移除。

## What Changes
- 移除 `PaddleExtractor._force_release_memory()` 方法及其所有调用点
- 移除 `pdf_extractor.py` 中的分批 OCR 处理逻辑（`OCR_BATCH_SIZE` 相关的分支、循环、进度回调、内存监控、批次间等待等）
- 移除 `_merge_batch_results()` 辅助函数
- 移除 `config.py` 中的 `OCR_BATCH_SIZE` 配置项
- 清理因移除而产生的无用 import（如 `time` 用于 `time.sleep(3)` 等）

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`、`modules/pdf_extractor.py`、`config.py`
- Affected specs: `ocr-three-layer-protection-and-batching`（分批处理部分移除）、`fix-batch-formula-memory-leak`（批次间内存释放部分移除）、`optimize-ocr-memory`（`malloc_trim` 部分移除）、`intel-mac-16gb-ocr-mem`（页面粒度管线销毁与 GC 部分移除）

## ADDED Requirements

无

## MODIFIED Requirements

### Requirement: OCR 提取统一为单次子进程调用
OCR 模式下，无论 PDF 页数多少，均使用单次 `run_ocr_in_subprocess()` 调用处理所有页面，不再分批。

#### Scenario: 大页数 PDF 处理
- **WHEN** 用户上传 800 页 PDF
- **THEN** 系统使用单次子进程调用处理所有页面，不再分割为多批

#### Scenario: 小页数 PDF 处理
- **WHEN** 用户上传 5 页 PDF
- **THEN** 行为与当前一致，单次子进程调用

## REMOVED Requirements

### Requirement: 分批 OCR 处理
**Reason**: C++ 底层不释放内存，分批处理无法降低内存峰值，每批仍需加载完整模型，反而增加总耗时和代码复杂度。
**Migration**: 所有 PDF 统一使用单次子进程调用。停滞检测（stall_timeout）和心跳超时仍作为保护机制。

### Requirement: 强制释放内存（`_force_release_memory` / `malloc_trim`）
**Reason**: PaddlePaddle C++ 内存池不受 `malloc_trim` / `malloc_zone_pressure_relief` 影响，强制释放无实际效果，仅产生误导性日志。
**Migration**: 保留 `del pipeline` + `gc.collect()` 释放 Python 层引用，移除 C++ 层强制释放尝试。

### Requirement: 批次间内存监控与等待
**Reason**: 无分批处理则无批次间监控需求。
**Migration**: 无需迁移。

### Requirement: `OCR_BATCH_SIZE` 配置项
**Reason**: 无分批处理则无需配置。
**Migration**: 移除环境变量 `OCR_BATCH_SIZE`，不再支持。
