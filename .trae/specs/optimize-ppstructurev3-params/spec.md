# PPStructureV3 推理参数优化 Spec

## Why

当前项目使用 PPStructureV3（非 PaddleOCR 直接调用），部分关键推理参数未显式设置，导致：`cpu_threads` 默认10与外部环境变量 `OMP_NUM_THREADS=2` 不一致引发线程竞争；文本检测分辨率未压缩（大图推理慢）；无噪点文本框过滤导致识别调用浪费；识别未批量执行。这些优化在 CPU 推理下收益显著。

## What Changes

- **对齐 cpu_threads**：将 `cpu_threads` 参数传入 PPStructureV3，与 `OMP_NUM_THREADS` 环境变量保持一致
- **压缩检测分辨率**：设置 `text_det_limit_side_len=960`，大图长边压缩减少40%推理耗时
- **调低检测阈值**：设置 `text_det_thresh=0.3`、`text_det_box_thresh=0.5`，减少冗余小文本框
- **批量识别**：设置 `text_recognition_batch_size=10`，利用向量化减少推理内核调用次数
- **识别置信度过滤**：设置 `text_rec_score_thresh=0.5`，过滤低置信度识别结果
- **后处理噪点框过滤**：在 `_process_page_layout` 中添加最小面积过滤，移除极小噪点文本框

## 不适用的建议（不纳入）

| 建议 | 原因 |
|------|------|
| `enable_mkldnn=True` | PPStructureV3 默认已开启；macOS Apple Silicon 上为 no-op |
| `mkldnn_cache_size=512` | macOS 上 MKLDNN 不可用，设置无意义 |
| `use_angle_cls=False` | 项目已通过 `use_textline_orientation=False` 禁用 |
| `use_gpu=False` | 项目已根据平台自动选择 CPU/GPU |
| `det_db_unclip_ratio=1.5` | PPStructureV3 中对应参数为 `text_det_unclip_ratio`，默认值已合理 |
| `rec_image_shape="3,32,320"` | PPStructureV3 不支持此参数（PaddleOCR v2 参数） |
| `use_memory_optim=True` | PPStructureV3 不支持此参数 |
| 图片预处理（灰度化/二值化） | PPStructureV3 内部已做归一化；对干净 PDF 渲染图收益低 |

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`、`modules/ocr/ocr_worker.py`
- Affected specs: `fix-formula-predict-gil-hang`（同属 OCR 流程优化）
- 行为变更：OCR 推理速度提升（预计30-50%），极小噪点文本框被过滤

## ADDED Requirements

### Requirement: 对齐 cpu_threads 参数

系统 SHALL 在创建 PPStructureV3 管线时，将 `cpu_threads` 参数与 OCR 子进程的 `OMP_NUM_THREADS` 环境变量保持一致，避免线程竞争。

#### Scenario: OCR 子进程使用2线程

- **WHEN** OCR 子进程设置 `OMP_NUM_THREADS=2`
- **THEN** PPStructureV3 管线创建时传入 `cpu_threads=2`
- **AND** PaddleX 推理引擎使用2个线程

### Requirement: 压缩文本检测分辨率

系统 SHALL 在创建 PPStructureV3 管线时设置 `text_det_limit_side_len=960`，将大图长边压缩到960像素，减少检测模型推理耗时。

#### Scenario: A4 文档页面检测

- **WHEN** 输入图片长边超过960像素
- **THEN** 检测模型将图片压缩到长边960后推理
- **AND** 检测速度显著提升

### Requirement: 调低检测阈值

系统 SHALL 设置 `text_det_thresh=0.3` 和 `text_det_box_thresh=0.5`，减少冗余小文本框的检测输出。

#### Scenario: 含噪点的扫描文档

- **WHEN** 扫描文档含背景噪点
- **THEN** 低置信度噪点框被检测阈值过滤
- **AND** 减少后续识别调用次数

### Requirement: 批量文本识别

系统 SHALL 设置 `text_recognition_batch_size=10`，将多个文本框一次性送入识别模型，利用向量化提升吞吐。

#### Scenario: 含多个文本框的页面

- **WHEN** 页面检测到20个文本框
- **THEN** 识别模型分2批处理（每批10个）
- **AND** 减少推理内核调用次数

### Requirement: 识别置信度过滤

系统 SHALL 设置 `text_rec_score_thresh=0.5`，过滤低置信度的识别结果。

#### Scenario: 模糊文本识别

- **WHEN** 识别模型对某文本框的置信度低于0.5
- **THEN** 该文本框被过滤，不进入后续处理

### Requirement: 后处理噪点框过滤

系统 SHALL 在 `_process_page_layout` 中添加最小面积过滤，移除面积过小的噪点文本框。

#### Scenario: 极小噪点框

- **WHEN** 检测输出的文本框面积小于页面面积的0.01%
- **THEN** 该文本框被过滤，不进入识别和后续处理

## MODIFIED Requirements

### Requirement: _create_pipeline 参数

`_create_pipeline()` 方法 SHALL 额外传入 `cpu_threads`、`text_det_limit_side_len`、`text_det_thresh`、`text_det_box_thresh`、`text_recognition_batch_size`、`text_rec_score_thresh` 参数。

## REMOVED Requirements

（无移除的需求）
