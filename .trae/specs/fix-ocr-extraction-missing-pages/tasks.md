# Tasks

- [x] Task 1: 修复 all_page_nums 排序问题
  - [x] SubTask 1.1: 在 `pdf_extractor.py` 中将 `all_page_nums = list(pages)` 改为 `all_page_nums = sorted(pages)`

- [x] Task 2: 步骤1.5单页超时保护
  - [x] SubTask 2.1: 在 `paddle_extractor.py` 步骤1.5逐页处理循环中，为 `pipeline.predict()` 添加超时保护（ThreadPoolExecutor + future.result(timeout=120)）
  - [x] SubTask 2.2: 超时后跳过该页，记录警告日志，通过 status_callback 通知用户
  - [x] SubTask 2.3: 跳过后继续处理后续页面（continue，不 break）

# Task Dependencies
- Task 1 和 Task 2 相互独立，已并行执行完成
