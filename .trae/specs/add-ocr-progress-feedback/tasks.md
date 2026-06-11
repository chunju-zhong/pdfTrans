# Tasks

- [x] Task 1: _run_ocr_once 和 run_ocr_in_subprocess 新增 progress_callback 参数
  - [x] SubTask 1.1: `_run_ocr_once` 函数签名新增 `progress_callback=None` 参数
  - [x] SubTask 1.2: `_run_ocr_once` 中收到 STEP_START 消息时调用 `progress_callback('step_start', payload)`
  - [x] SubTask 1.3: `_run_ocr_once` 中收到 STEP_PROGRESS 消息时调用 `progress_callback('step_progress', payload)`
  - [x] SubTask 1.4: `_run_ocr_once` 中收到 STEP_COMPLETE 消息时调用 `progress_callback('step_complete', payload)`
  - [x] SubTask 1.5: `run_ocr_in_subprocess` 函数签名新增 `progress_callback=None` 参数，透传给 `_run_ocr_once`

- [x] Task 2: PdfExtractor.extract 新增 progress_callback 参数并传递
  - [x] SubTask 2.1: `PdfExtractor.extract` 方法签名新增 `progress_callback=None` 参数
  - [x] SubTask 2.2: OCR 模式下单批调用 `run_ocr_in_subprocess` 时传递 `progress_callback`
  - [x] SubTask 2.3: OCR 模式下分批调用时，包装 `progress_callback` 以在消息中添加批次信息（第X/Y批）

- [x] Task 3: translation_service 桥接 Task 进度更新
  - [x] SubTask 3.1: `extract_pdf_content` 方法中，OCR 模式下创建 progress_callback 闭包，将 OCR 进度转换为 `task.update_phase_progress('extraction', percent, message)` 调用
  - [x] SubTask 3.2: 进度百分比计算：根据批次进度（batch_idx/total_batches）和步骤内进度（pages_done/total_pages）按权重计算 extraction 阶段百分比
  - [x] SubTask 3.3: 进度消息格式化：单批时 "OCR提取: 步骤名 X/Y页"，分批时 "OCR提取: 第A/B批 - 步骤名 X/Y页"

# Task Dependencies
- Task 1 是基础，Task 2 依赖 Task 1，Task 3 依赖 Task 2
- Task 1 → Task 2 → Task 3 顺序执行
