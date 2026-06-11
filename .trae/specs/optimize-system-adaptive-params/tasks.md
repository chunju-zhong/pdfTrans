# Tasks

- [x] Task 1: 扩展 OcrParameterCalculator 输出模型名称和推理参数
  - [x] SubTask 1.1: 在 `system_profiler.py` 中添加 `compute_model_names()` 方法，根据内存分级返回模型名称映射
  - [x] SubTask 1.2: 在 `system_profiler.py` 中添加 `compute_inference_params()` 方法，根据内存分级返回推理参数（batch_size、det_limit_side_len）
  - [x] SubTask 1.3: 在 `compute_all_params()` 中整合新方法输出，添加 `model_names`、`inference_params`、`use_gpu`、`render_dpi` 字段
  - [x] SubTask 1.4: 恢复 `should_skip_table()` 和 `should_skip_formula()` 的条件逻辑，**基于 `total_memory_gb` 判断**：`should_skip_formula()` 在 total ≤ 8GB 时返回 True；`should_skip_table()` 在 total ≤ 4GB 时返回 True

- [x] Task 2: 启用 GPU 自适应
  - [x] SubTask 2.1: 修改 `ocr_worker.py` 的 `_ocr_worker_func`，根据 `ocr_params['use_gpu']` 决定是否强制 CPU 模式
  - [x] SubTask 2.2: 当 `use_gpu=True` 时，不设置 `CUDA_VISIBLE_DEVICES=-1`、`PADDLE_ONLY_CPU=1`、`PADDLE_WITH_GPU=OFF`
  - [x] SubTask 2.3: 当 `use_gpu=True` 时，传入 `use_gpu=True` 给 PaddleOcrExtractor

- [x] Task 3: 模型名称自适应
  - [x] SubTask 3.1: 修改 `paddle_extractor.py` 的 `_create_pipeline()`，从 `self.model_names` 读取模型名称并传入 PPStructureV3
  - [x] SubTask 3.2: 在 `__init__` 中存储 `self.model_names` 从 `ocr_params`
  - [x] SubTask 3.3: 当 `use_formula=True` 时，使用 `model_names['formula']` 替代硬编码的 `PP-FormulaNet_plus-S`

- [x] Task 4: 推理参数自适应
  - [x] SubTask 4.1: 修改 `paddle_extractor.py` 的 `_create_pipeline()`，从 `self.inference_params` 读取 `text_recognition_batch_size` 和 `text_det_limit_side_len`，替代硬编码值
  - [x] SubTask 4.2: 在 `__init__` 中存储 `self.inference_params` 从 `ocr_params`

- [x] Task 5: 修复 render_dpi 未消费
  - [x] SubTask 5.1: 修改 `paddle_extractor.py` 的 `_render_pages()`，使用 `ocr_params['render_dpi']` 替代 `config.OCR_RENDER_DPI`
  - [x] SubTask 5.2: 在 `__init__` 中存储 `self.render_dpi` 从 `ocr_params`

- [x] Task 6: 修复 OCR_BATCH_SIZE 不一致
  - [x] SubTask 6.1: 修改 `pdf_extractor.py` 中 `getattr(app_config, 'OCR_BATCH_SIZE', 20)` 的 fallback 从 20 改为与 config.py 一致的值

# Task Dependencies

- [Task 1] 独立，必须首先完成（其他任务依赖其输出格式）
- [Task 2] 依赖 [Task 1]（需要 profiler 输出的 use_gpu 字段）
- [Task 3] 依赖 [Task 1]（需要 profiler 输出的 model_names 字段）
- [Task 4] 依赖 [Task 1]（需要 profiler 输出的 inference_params 字段）
- [Task 5] 依赖 [Task 1]（需要 profiler 输出的 render_dpi 字段）
- [Task 6] 独立
