# Tasks

- [x] Task 1: 显式使用 spawn 上下文创建 OCR 子进程
  - [x] SubTask 1.1: 修改 `modules/ocr/ocr_worker.py`，使用 `multiprocessing.get_context('spawn')` 创建 Process 和 Queue

- [x] Task 2: PaddlePaddle 环境变量优化
  - [x] SubTask 2.1: 在 `_ocr_worker_func` 开头、导入 PaddlePaddle 之前设置 `FLAGS_fraction_of_gpu_memory_to_use=0.5` 和 `CPU_NUM=2`

- [x] Task 3: 禁用不必要的模型
  - [x] SubTask 3.1: 修改 `_create_pipeline()` 方法，添加 `use_region_detection` 参数，默认为 `False`
  - [x] SubTask 3.2: 在所有 `_create_pipeline()` 调用中传递 `use_region_detection=False`

- [x] Task 4: 降低渲染 DPI
  - [x] SubTask 4.1: 修改 `_render_pages()` 方法，将 DPI 从 200 降低到 150

- [x] Task 5: 添加内存监控日志
  - [x] SubTask 5.1: 在 `_ocr_worker_func` 开头记录初始内存
  - [x] SubTask 5.2: 在 `extract_from_pdf()` 每个步骤前后记录 RSS 内存使用量
  - [x] SubTask 5.3: 在 `_create_pipeline()` 创建前后记录内存

- [x] Task 6: 优化步骤2/3的管线配置
  - [x] SubTask 6.1: 步骤2创建管线时传递 `use_formula_recognition=False, use_region_detection=False`
  - [x] SubTask 6.2: 步骤3创建管线时传递 `use_table_recognition=False, use_region_detection=False`

# Task Dependencies

- [Task 3] depends on [Task 6]（两者都修改 _create_pipeline，一起实施）
- 其余任务无依赖，可并行实施
