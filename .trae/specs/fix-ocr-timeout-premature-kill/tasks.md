# Tasks

- [x] Task 1: 移除 system_profiler.py 中的 3600 秒硬编码上限
  - [x] SubTask 1.1: 修改 `compute_timeout_params` 方法，移除 `min(max_total_time, 3600)` 中的硬编码 3600，改为不截断（让调用方根据 config 上限截断）
- [x] Task 2: 让 config.OCR_MAX_TOTAL_TIME 在 run_ocr_in_subprocess 中生效
  - [x] SubTask 2.1: 在 `run_ocr_in_subprocess` 中，当动态参数计算出 `max_total_time` 后，用 `config.OCR_MAX_TOTAL_TIME` 作为上限截断：`max_total_time = min(max_total_time, config.OCR_MAX_TOTAL_TIME)`
  - [x] SubTask 2.2: 将 config.py 中 `OCR_MAX_TOTAL_TIME` 从 1800 改为 7200（2小时），以适应大页数 PDF
- [x] Task 3: 在 _run_ocr_once 中实现动态延长超时
  - [x] SubTask 3.1: 当收到 `STATUS_STEP_PROGRESS` 消息时，根据已完成页数和已用时间估算剩余时间，若剩余时间不足则动态延长 `max_total_time`
  - [x] SubTask 3.2: 动态延长的上限为 `config.OCR_MAX_TOTAL_TIME * 2`，防止无限延长
- [x] Task 4: 重试时增加超时预算
  - [x] SubTask 4.1: 在 `_degrade_params` 中增加对 `timeout_params.max_total_time` 的调整，每次重试增加 50%
  - [x] SubTask 4.2: 在重试循环中，使用降级后的 `max_total_time`

# Task Dependencies
- Task 2 依赖 Task 1（需要先移除硬编码上限，才能让 config 上限生效）
- Task 3 依赖 Task 2（动态延长需要知道 config 上限）
- Task 4 独立于 Task 3，可与 Task 3 并行
