# 优化OCR内存使用与修复段错误 Spec

## Why

上轮修复（分步加载+进程隔离）后，OCR 子进程仍然以 exitcode=-11 (SIGSEGV) 崩溃。深度调查发现：PaddlePaddle 内部强制使用 `fork` 上下文（在 macOS 上不安全）、Python 3.13 兼容性风险、C++ 层内存未真正释放、以及 RegionDetection 等不必要的模型默认加载，都是导致崩溃的因素。

## 硬件约束

- CPU: 2.6 GHz 6-Core Intel Core i7
- GPU: Intel UHD Graphics 630 1536 MB（无CUDA，仅CPU模式）
- 内存: 16 GB 2400 MHz DDR4
- macOS 对 Python 进程默认内存限制约4GB

## What Changes

- 显式使用 `spawn` 上下文创建 OCR 子进程，避免 PaddlePaddle 内部 fork 导致的 macOS 崩溃
- 在子进程中设置 PaddlePaddle 环境变量，限制 CPU 线程数和内存占用
- 禁用 RegionDetection 模型（默认加载但不必要）
- 降低 PDF 渲染 DPI（200→150），减少图像内存占用
- 添加详细的内存监控日志，精确定位崩溃时刻
- 优化分步加载策略：步骤2/3 复用步骤1 的版面分析结果，避免重复加载版面分析模型

## Impact

- Affected specs: OCR功能
- Affected code: `modules/ocr/paddle_extractor.py`, `modules/ocr/ocr_worker.py`

## ADDED Requirements

### Requirement: 显式使用 spawn 上下文

系统 SHALL 在创建 OCR 子进程时显式使用 `multiprocessing.get_context('spawn')`，避免 PaddlePaddle 内部 fork 上下文在 macOS 上导致的段错误。

#### Scenario: macOS 上创建 OCR 子进程

- **WHEN** 在 macOS 上启动 OCR 子进程
- **THEN** 使用 `spawn` 上下文创建 `Process` 和 `Queue`
- **AND** 不使用默认的 `multiprocessing.Process()`（可能受 PaddlePaddle 全局设置影响）

### Requirement: PaddlePaddle 环境变量优化

系统 SHALL 在 OCR 子进程工作函数开头设置以下环境变量，限制内存和 CPU 占用：

- `FLAGS_fraction_of_gpu_memory_to_use=0.5` — 限制 GPU 内存使用比例
- `CPU_NUM=2` — 限制 PaddlePaddle 使用的 CPU 线程数，减少内存峰值

#### Scenario: 子进程启动时设置环境变量

- **WHEN** OCR 子进程工作函数开始执行
- **THEN** 在导入 PaddlePaddle 之前设置上述环境变量
- **AND** 环境变量在子进程生命周期内有效

### Requirement: 禁用不必要的模型

系统 SHALL 在创建 PPStructureV3 管线时禁用 RegionDetection 模型，减少内存占用约 300MB。

#### Scenario: 步骤1创建管线

- **WHEN** 创建版面分析+文本OCR管线
- **THEN** 传递 `use_region_detection=False` 给 PPStructureV3
- **AND** RegionDetection 模型不被加载

### Requirement: 降低渲染 DPI

系统 SHALL 将 PDF 页面渲染 DPI 从 200 降低到 150，减少图像内存占用约 44%（像素数从 200^2 降至 150^2）。

#### Scenario: 渲染 PDF 页面

- **WHEN** 将 PDF 页面渲染为图像用于 OCR
- **THEN** 使用 150 DPI 渲染
- **AND** OCR 识别精度仍在可接受范围内

### Requirement: 内存监控日志

系统 SHALL 在 OCR 子进程的关键步骤添加内存使用日志，帮助定位崩溃时刻。

#### Scenario: 每个步骤前后记录内存

- **WHEN** OCR 子进程执行每个步骤（管线创建、推理、释放）
- **THEN** 记录当前进程的 RSS 内存使用量
- **AND** 日志格式为 "步骤X: 内存使用 XXXX MB"

### Requirement: 优化步骤2/3避免重复加载版面分析模型

当前步骤2（表格识别）和步骤3（公式识别）各自创建完整的 PPStructureV3 实例，会重复加载版面分析+OCR模型。系统 SHALL 优化为：步骤2/3仅对有对应区域的页面运行推理，且在创建管线时禁用不需要的功能以减少模型加载。

#### Scenario: 步骤2创建表格识别管线

- **WHEN** 步骤2创建表格识别管线
- **THEN** 传递 `use_formula_recognition=False, use_region_detection=False` 减少模型加载
- **AND** 仅加载版面分析+OCR+表格识别模型

#### Scenario: 步骤3创建公式识别管线

- **WHEN** 步骤3创建公式识别管线
- **THEN** 传递 `use_table_recognition=False, use_region_detection=False` 减少模型加载
- **AND** 仅加载版面分析+OCR+公式识别模型

## MODIFIED Requirements

### Requirement: _create_pipeline 增加 use_region_detection 参数

`_create_pipeline()` 方法 SHALL 接受 `use_region_detection` 参数，默认为 `False`：

```python
def _create_pipeline(self, use_table=False, use_formula=False, use_region_detection=False):
```

## REMOVED Requirements

无
