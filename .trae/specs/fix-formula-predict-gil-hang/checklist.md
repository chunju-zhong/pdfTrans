# Checklist

## 移除步骤1.5

- [x] 步骤1.5 的整个 for 循环代码已移除
- [x] 步骤1.5 的 status_callback 调用已移除
- [x] 步骤1.5 相关变量已移除（formula_detect_aborted、formula_detect_pages_done、FORMULA_DETECT_PAGE_TIMEOUT）
- [x] 步骤1完成后日志记录哪些页面检测到公式

## 换用 PP-FormulaNet_plus-S 小模型

- [x] `_create_pipeline()` 在 `use_formula=True` 时传入 `formula_recognition_model_name="PP-FormulaNet_plus-S"`
- [x] 日志中确认加载的是 PP-FormulaNet_plus-S 模型（非默认的 M 模型）

## 移除步骤3超时机制

- [x] 步骤3的 ThreadPoolExecutor 包装代码已移除
- [x] FORMULA_RECOGNIZE_PAGE_TIMEOUT 常量已移除
- [x] 步骤3改为直接调用 `pipeline.predict(img_array)`
- [x] 不再需要的导入（ThreadPoolExecutor、FuturesTimeoutError）已移除

## 禁用心跳超时

- [x] `config.py` 中 `OCR_HEARTBEAT_TIMEOUT` 默认值改为 `'0'`
- [x] `ocr_worker.py` 中 `heartbeat_timeout` 默认值改为 `0`
- [x] `ocr_worker.py` 心跳超时检查增加 `heartbeat_timeout > 0` 条件，为0时跳过
- [x] 非零值时心跳超时检查仍正常工作

## 诊断日志

- [x] 步骤1完成时记录哪些页面检测到公式
- [x] 步骤3每页记录 predict 执行耗时（开始时间、结束时间、耗时秒数）

## 端到端验证

- [ ] 含公式页面不再被心跳超时杀掉
- [ ] 步骤1正确检测公式区域（`has_formula=True`）
- [ ] 步骤3使用 PP-FormulaNet_plus-S 模型能完成公式识别
- [ ] 整个 OCR 流程能正常完成
