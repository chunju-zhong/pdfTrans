# Tasks

- [x] Task 1: 修改 paddle_extractor.py 中的回调 payload
  - [x] SubTask 1.1: 在步骤 1 的 step_progress 回调中添加 `'step_name': self.STEP_LAYOUT_OCR_NAME`
  - [x] SubTask 1.2: 步骤 2 的 step_start 回调移除 `total_pages` 字段

- [x] Task 2: 修复 _ocr_progress_cb 逻辑（translation_service.py）
  - [x] SubTask 2.1: 移除 `message = payload.get('message')` 死代码和 `if message` 分支
  - [x] SubTask 2.2: 统一消息格式：step_start 显示"OCR提取: {step_name}开始"，step_progress 显示"OCR提取: {step_name} {pages_done}/{total_pages}页"，step_complete 显示"OCR提取: {step_name}完成"
  - [x] SubTask 2.3: step_start 时 phase_percent 使用前面步骤的累积权重（_prior_weights），避免 phase_percent=0 导致进度倒退到 5%

# Task Dependencies
- Task 1 和 Task 2 可并行
