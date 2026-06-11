# Tasks

- [x] Task 1: 重构步骤2为逐页执行 + 新增 `page_result` 消息
  - [x] 在 `ocr_worker.py` 中新增 `STATUS_PAGE_RESULT = 'page_result'` 常量
  - [x] 修改 `PaddleOcrExtractor.extract_from_pdf`：将步骤2从"所有页面步骤1完成后统一执行"改为"每页步骤1完成后立即执行该页的步骤2"
  - [x] 每页步骤1+步骤2完成后，通过 `status_callback` 发送 `('page_result', {page_num, text_blocks, tables, images})` 消息
  - [x] `text_blocks`、`tables`、`images` 需序列化为 dict（通过 `status_queue` 传递）
  - [x] 移除步骤2的独立 `step_start`/`step_complete` 回调，改为在步骤1的逐页进度中包含步骤2

- [x] Task 2: 修改 `_ocr_worker_func` 支持 `skip_pages` 参数
  - [x] `_ocr_worker_func` 增加 `skip_pages` 参数
  - [x] 将 `skip_pages` 传给 `PaddleOcrExtractor.extract_from_pdf`
  - [x] 子进程完成后通过 `result_queue` 发送 `('success', result.to_dict())` 作为完成确认

- [x] Task 3: 修改 `_run_ocr_once` 支持流式结果累积与 result_queue 检查
  - [x] 增加 `skip_pages` 参数，传给子进程
  - [x] 在监控循环中处理 `page_result` 消息，累积到 `completed_pages` 字典
  - [x] 在监控循环中非阻塞检查 `result_queue`，有完成确认则立即退出
  - [x] 子进程退出后，检查 `result_queue`：有完成确认则返回完整结果，无则返回已累积的部分结果
  - [x] 返回值改为 `(completed_pages_dict, completed_page_nums)` 元组
  - [x] 心跳超时和停滞超时仅在 `process.is_alive()` 为 True 时检查

- [x] Task 4: 修改 `run_ocr_in_subprocess` 支持断点续传
  - [x] 在重试循环中维护 `completed_pages` 字典和 `completed_page_nums` 列表
  - [x] 每次尝试后，将新完成的页面结果合并到 `completed_pages`
  - [x] 重试时，将 `completed_page_nums` 作为 `skip_pages` 传给 `_run_ocr_once`
  - [x] 所有页面完成后（或重试耗尽），从 `completed_pages` 组装最终 `PdfExtraction` 结果
  - [x] 全局编号 `table_idx`/`image_idx` 在最终组装时统一分配

- [x] Task 5: 修改 `PaddleOcrExtractor.extract_from_pdf` 支持 `skip_pages`
  - [x] 增加 `skip_pages` 参数（默认 `None`）
  - [x] 步骤1循环中，跳过 `skip_pages` 中的页面（但仍需渲染图像供步骤2使用）
  - [x] 对于跳过的页面，不执行步骤1和步骤2，不发送 `page_result`

# Task Dependencies
- Task 2 依赖 Task 1（需要 `page_result` 消息类型和新的 `result_queue` 格式）
- Task 3 依赖 Task 1（需要处理 `page_result` 消息）
- Task 4 依赖 Task 3（需要 `_run_ocr_once` 返回部分结果）
- Task 5 可与 Task 2 并行
