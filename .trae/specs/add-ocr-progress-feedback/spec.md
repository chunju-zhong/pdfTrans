# OCR 提取进度反馈到前端 Spec

## Why
OCR 提取大 PDF 时可能运行数十分钟，但前端只显示"正在提取PDF文本..."的静态消息，用户无法判断 OCR 是否在正常推进、当前处理到哪一步。后端已有完善的步骤级进度消息（step_start/step_progress/step_complete），但仅在 `_run_ocr_once` 内部用于日志和超时判断，未传递给 Task 对象和前端。

## What Changes
- 在 `run_ocr_in_subprocess` 和 `_run_ocr_once` 中新增 `progress_callback` 参数，将 OCR 步骤级进度向上层传递
- 在 `pdf_extractor.extract()` 中创建进度回调，传递给 `run_ocr_in_subprocess`
- 在 `translation_service.extract_pdf_content()` 中将 Task 对象的进度更新方法桥接到 PdfExtractor
- 分批处理时，进度消息包含批次信息（第X/Y批）
- 前端无需修改，已有轮询机制自动获取 `task.message` 更新

## Impact
- Affected code: `modules/ocr/ocr_worker.py`、`modules/pdf_extractor.py`、`services/translation_service.py`
- Affected specs: ocr-three-layer-protection-and-batching（分批进度消息格式需兼容）

## ADDED Requirements

### Requirement: OCR 进度回调传递
系统 SHALL 在 OCR 子进程运行期间，将步骤级进度消息通过回调函数传递到 Task 对象，使前端能实时显示 OCR 处理状态。

#### Scenario: OCR 正常提取进度
- **WHEN** OCR 子进程发送 STEP_PROGRESS 消息（如步骤1版面分析 15/20页）
- **THEN** Task 对象的 message 更新为 "OCR提取: 版面分析+文本OCR 15/20页"，progress 在 extraction 阶段区间内按比例更新

#### Scenario: OCR 步骤切换
- **WHEN** OCR 子进程发送 STEP_START 消息（如步骤2表格识别开始）
- **THEN** Task 对象的 message 更新为 "OCR提取: 表格识别 0/20页"

#### Scenario: 分批 OCR 进度
- **WHEN** 800 页 PDF 分 40 批处理，第 3 批步骤1进度为 10/20 页
- **THEN** Task 对象的 message 更新为 "OCR提取: 第3/40批 - 版面分析+文本OCR 10/20页"

#### Scenario: 非 OCR 模式不受影响
- **WHEN** 使用普通 PyMuPDF 提取（ocr_mode=False）
- **THEN** 进度显示与当前行为完全一致，不受任何影响

### Requirement: 进度百分比计算
OCR 提取阶段（extraction phase 10%-35%）的进度百分比 SHALL 根据实际 OCR 处理进度按比例计算，而非仅依赖提取后的页面遍历。

#### Scenario: 单批 OCR 进度计算
- **WHEN** OCR 处理 20 页 PDF，步骤1完成 10/20 页
- **THEN** extraction 阶段进度约为 25%（步骤1占50%权重，10/20=50%，50%×50%=25%）

#### Scenario: 分批 OCR 进度计算
- **WHEN** 800 页 PDF 分 40 批，第 2 批完成
- **THEN** extraction 阶段进度约为 5%（2/40=5%）

## MODIFIED Requirements

### Requirement: run_ocr_in_subprocess 支持进度回调
`run_ocr_in_subprocess` 函数签名新增 `progress_callback` 可选参数（默认 None）。当提供时，`_run_ocr_once` 在收到 STEP_START/STEP_PROGRESS/STEP_COMPLETE 消息时调用该回调。

### Requirement: PdfExtractor.extract 支持进度回调
`PdfExtractor.extract` 方法签名新增 `progress_callback` 可选参数（默认 None）。在 OCR 模式下，将此回调传递给 `run_ocr_in_subprocess`；在非 OCR 模式下忽略。
