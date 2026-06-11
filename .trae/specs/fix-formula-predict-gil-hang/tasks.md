# Tasks

- [x] Task 1: 移除步骤1.5 全部代码
  - [x] SubTask 1.1: 移除步骤1.5 的整个 for 循环代码块（约第790-870行）
  - [x] SubTask 1.2: 移除步骤1.5 的 status_callback 调用
  - [x] SubTask 1.3: 移除步骤1.5 相关变量（formula_detect_aborted、formula_detect_pages_done、FORMULA_DETECT_PAGE_TIMEOUT）
  - [x] SubTask 1.4: 在步骤1完成后的日志中增加哪些页面检测到公式的信息

- [x] Task 2: 换用 PP-FormulaNet_plus-S 小模型
  - [x] SubTask 2.1: 在 `_create_pipeline()` 方法中，当 `use_formula=True` 时传入 `formula_recognition_model_name="PP-FormulaNet_plus-S"` 参数

- [x] Task 3: 移除步骤3的 ThreadPoolExecutor 超时，改为直接调用
  - [x] SubTask 3.1: 移除步骤3的 ThreadPoolExecutor 包装代码和 FORMULA_RECOGNIZE_PAGE_TIMEOUT 常量
  - [x] SubTask 3.2: 改为直接调用 `pipeline.predict(img_array)`
  - [x] SubTask 3.3: 移除不再需要的 ThreadPoolExecutor 和 FuturesTimeoutError 导入（如果步骤1.5移除后已无其他使用）
  - [x] SubTask 3.4: 添加诊断日志（predict 开始时间、结束时间、耗时秒数）

- [x] Task 4: 禁用心跳超时
  - [x] SubTask 4.1: 在 `config.py` 中将 `OCR_HEARTBEAT_TIMEOUT` 默认值从 `'90'` 改为 `'0'`
  - [x] SubTask 4.2: 在 `ocr_worker.py` 中将 `heartbeat_timeout` 默认值从 `90` 改为 `0`
  - [x] SubTask 4.3: 在 `ocr_worker.py` 心跳超时检查处（第273行），增加 `heartbeat_timeout > 0` 条件，为0时跳过检查

# Task Dependencies

- [Task 1] 独立，可首先实施
- [Task 2] 独立，可与 Task 1 并行
- [Task 3] 依赖 [Task 1]（移除步骤1.5后步骤3的代码位置和上下文会变化）
- [Task 4] 独立，可与 Task 1-3 并行
