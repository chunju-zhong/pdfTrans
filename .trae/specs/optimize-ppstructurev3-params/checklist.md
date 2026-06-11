# Checklist

## cpu_threads 对齐

- [x] `_create_pipeline()` 传入 `cpu_threads` 参数
- [x] `cpu_threads` 值与 `OMP_NUM_THREADS` 环境变量一致
- [x] 不再出现 PaddleX 默认10线程与外部2线程不一致的情况

## 推理优化参数

- [x] `text_det_limit_side_len=960` 已设置
- [x] `text_det_thresh=0.3` 已设置
- [x] `text_det_box_thresh=0.5` 已设置
- [x] `text_recognition_batch_size=10` 已设置
- [x] `text_rec_score_thresh=0.5` 已设置

## 噪点框过滤

- [x] 面积小于页面面积0.01%的文本框被过滤
- [x] 正常大小的文本框不受影响

## 端到端验证

- [ ] OCR 推理速度有提升（对比优化前后耗时）
- [ ] 文本识别准确率无明显下降
- [ ] 表格和公式识别不受影响
