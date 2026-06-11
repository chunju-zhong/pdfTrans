# Tasks

- [x] Task 1: 对齐 cpu_threads 参数
  - [x] SubTask 1.1: 在 `ocr_worker.py` 中将 `OMP_NUM_THREADS` 值通过 `ocr_params` 传递给 OCR 子进程的 `paddle_extractor`
  - [x] SubTask 1.2: 在 `paddle_extractor.py` 的 `_create_pipeline()` 中读取线程数并传入 `cpu_threads` 参数

- [x] Task 2: 添加 PPStructureV3 推理优化参数
  - [x] SubTask 2.1: 在 `_create_pipeline()` 中添加 `text_det_limit_side_len=960`
  - [x] SubTask 2.2: 在 `_create_pipeline()` 中添加 `text_det_thresh=0.3`
  - [x] SubTask 2.3: 在 `_create_pipeline()` 中添加 `text_det_box_thresh=0.5`
  - [x] SubTask 2.4: 在 `_create_pipeline()` 中添加 `text_recognition_batch_size=10`
  - [x] SubTask 2.5: 在 `_create_pipeline()` 中添加 `text_rec_score_thresh=0.5`

- [x] Task 3: 后处理噪点框过滤
  - [x] SubTask 3.1: 在 `_process_page_layout()` 中添加最小面积过滤逻辑，过滤面积小于页面面积0.01%的文本框

# Task Dependencies

- [Task 1] 独立
- [Task 2] 独立，可与 Task 1 并行
- [Task 3] 独立，可与 Task 1-2 并行
