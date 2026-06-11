# 修复 OCR 提取页面缺失 Spec

## Why
OCR 分批提取时，`all_page_nums = list(pages)` 使用了 `set` 转 `list` 的无序性，导致页码顺序混乱（如 [32,...,40,30,31] 而非 [30,...,40]）。当某批中某一页卡死时，整个批次丢失，但缺失页码报告中的页码与用户预期不符。同时步骤1.5处理某些页面时 `pipeline.predict()` 卡死导致子进程心跳中断，3次重试全部失败后整批页面丢失。

## What Changes
- 修复 `all_page_nums` 排序问题：`list(pages)` → `sorted(pages)`
- 步骤1.5增加超时保护：单页 predict 超时后跳过该页继续处理后续页面

## Impact
- Affected code: `modules/pdf_extractor.py`, `modules/ocr/paddle_extractor.py`
- Affected specs: 无

## ADDED Requirements

### Requirement: all_page_nums 排序
分批 OCR 时，`all_page_nums` SHALL 按页码升序排列，确保分批结果与用户预期一致。

#### Scenario: 页码排序
- **WHEN** 用户请求翻译 30-40 页
- **THEN** `all_page_nums = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]`
- **AND** 第1批 = [30, 31, 32, 33, 34]，第2批 = [35, 36, 37, 38, 39]，第3批 = [40]

### Requirement: 步骤1.5单页超时保护
步骤1.5逐页处理时，单页 predict 超过指定时间后 SHALL 跳过该页继续处理后续页面，而非卡死导致整批丢失。

#### Scenario: 单页超时跳过
- **WHEN** 步骤1.5处理某页时 `pipeline.predict()` 超过 120 秒
- **THEN** 跳过该页，记录警告日志，继续处理后续页面
- **AND** 该页的 `has_formula` 保持默认值 False

#### Scenario: 单页超时通知用户
- **WHEN** 步骤1.5跳过某页的公式检测
- **THEN** 通过 `status_callback` 发送进度消息，告知用户该页公式检测被跳过

## MODIFIED Requirements

### Requirement: pdf_extractor.py 分批排序
将 `all_page_nums = list(pages)` 改为 `all_page_nums = sorted(pages)`。

### Requirement: paddle_extractor.py 步骤1.5超时保护
在步骤1.5逐页处理循环中，为 `pipeline.predict()` 添加超时保护：
- 使用 `signal.alarm`（Unix）或 `multiprocessing.Queue` + 超时线程实现单页超时
- 超时后跳过该页，不设置 `has_formula`
- 跳过后继续处理后续页面

## REMOVED Requirements

无
