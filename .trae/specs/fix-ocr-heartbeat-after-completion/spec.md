# OCR 流式识别与断点续传 Spec

## Why
OCR 子进程完成提取后，将全部结果一次性放入 `result_queue` 并停止心跳线程，但父进程监控循环不检查 `result_queue`，导致心跳超时误报。更根本的问题是：如果子进程在处理第 60 页时崩溃，前 41 页的结果全部丢失，重试必须从头开始。应改为流式识别：每页完成步骤1+步骤2后立即将结果传回父进程，子进程崩溃时已完成的页面结果不丢失，重试可从中断位置继续。

## What Changes
- 新增 `STATUS_PAGE_RESULT` 消息类型，子进程每完成一页（步骤1版面分析+步骤2图像裁剪）后，立即通过 `status_queue` 将该页完整结果传回父进程
- 将步骤2（图像裁剪）从"所有页面步骤1完成后统一执行"改为"每页步骤1完成后立即执行该页的步骤2"，实现逐页完整处理
- 父进程在监控循环中累积已完成的页面结果
- 子进程全部完成后，通过 `result_queue` 发送完成确认（`('success', {total_pages, completed_page_nums})`），不再发送大量数据
- 父进程在监控循环内检查 `result_queue`，收到完成确认后立即退出
- 重试时，将已完成的页码列表传给子进程，子进程跳过这些页面
- 合并多次尝试的结果：首次尝试的页面结果 + 重试补充的页面结果

## Impact
- Affected code: `modules/ocr/ocr_worker.py`（`_run_ocr_once`、`_ocr_worker_func`、`run_ocr_in_subprocess`）、`modules/ocr/paddle_extractor.py`（`extract_from_pdf` 重构步骤2为逐页执行、增加 `skip_pages` 参数）
- Affected specs: `fix-ocr-timeout-premature-kill`（心跳超时逻辑简化）

## ADDED Requirements

### Requirement: 逐页完整处理并流式回传
子进程 SHALL 对每页依次执行步骤1（版面分析+文本+公式+表格）和步骤2（图像裁剪），完成后立即通过 `status_queue` 发送 `page_result` 消息，包含该页的完整结果（`page_num`、`text_blocks`、`tables`、`images`）。

#### Scenario: 逐页完成
- **WHEN** 子进程完成第 N 页的步骤1+步骤2
- **THEN** 通过 `status_queue` 发送 `('page_result', {page_num, text_blocks, tables, images})` 消息

### Requirement: 父进程累积流式结果
父进程 SHALL 在监控循环中接收并累积每页结果。子进程完成或崩溃后，父进程拥有已完成页面的数据。

#### Scenario: 子进程正常完成
- **WHEN** 子进程完成所有页面并通过 `result_queue` 发送完成确认
- **THEN** 父进程在监控循环中检测到 `result_queue` 有数据，立即读取并返回完整结果

#### Scenario: 子进程中途崩溃
- **WHEN** 子进程在第 60 页崩溃，前 41 页已通过 `page_result` 消息传回
- **THEN** 父进程检测到子进程退出且 `result_queue` 为空，将已累积的 41 页结果保存，触发重试

### Requirement: 父进程在监控循环内检查 result_queue
父进程 SHALL 在每次监控循环迭代中非阻塞检查 `result_queue`，一旦子进程放入完成确认，立即读取并退出循环。

#### Scenario: 子进程完成提取
- **WHEN** 子进程将完成确认放入 `result_queue`
- **THEN** 父进程在下一个循环迭代中检测到结果，立即退出监控循环

### Requirement: 断点续传——重试跳过已完成页面
重试时，`run_ocr_in_subprocess` SHALL 将已完成的页码列表传给子进程，子进程跳过这些页面，只处理剩余页面。

#### Scenario: 部分页面已完成，重试补充剩余
- **WHEN** 首次尝试完成了 41 页，子进程在第 60 页崩溃
- **THEN** 重试时传入 `skip_pages=[1..41]`，子进程只处理第 42 页及之后的页面
- **THEN** 重试成功后，合并首次 41 页和重试补充的页面结果

### Requirement: 合并多次尝试结果
`run_ocr_in_subprocess` SHALL 合并多次尝试的页面结果。后尝试的结果覆盖同页码的先尝试结果（以最新为准）。

#### Scenario: 合并首次和重试结果
- **WHEN** 首次尝试返回 41 页结果，重试返回 20 页结果（包含 41 页之后的页面）
- **THEN** 最终结果包含所有 61 页，无重复

## MODIFIED Requirements

### Requirement: 心跳超时仅在子进程存活时检查
心跳超时和停滞超时检查 SHALL 仅在子进程仍存活时执行。如果子进程已退出，不再检查心跳，而是直接检查 `result_queue`。

### Requirement: PaddleOcrExtractor 支持 skip_pages
`PaddleOcrExtractor.extract_from_pdf` SHALL 接受 `skip_pages` 参数（已完成的页码列表），跳过这些页面的处理。

### Requirement: 步骤2改为逐页执行
步骤2（图像裁剪）SHALL 从"所有页面步骤1完成后统一执行"改为"每页步骤1完成后立即执行该页的步骤2"，实现逐页完整处理。

## REMOVED Requirements

无
