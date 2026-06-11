# 系统性能自适应模型与参数优化 Spec

## Why

当前系统虽有 `system_profiler.py` 做性能分级，但模型选择、GPU 使用、推理参数等关键配置均为硬编码，未根据系统资源动态适配。GPU 检测代码存在但从未使用（子进程强制 CPU 模式）；模型大小（S/M/L）不随系统资源变化；推理参数（batch\_size、det\_limit\_side\_len）固定不变；profiler 计算的 render\_dpi 未被消费；feature skipping 逻辑被注释掉。

## What Changes

* **启用 GPU 自适应**：当系统有可用 GPU 时，OCR 子进程使用 GPU 推理

* **模型大小自适应**：根据内存分级选择不同大小的模型（layout、formula、text det/rec）

* **推理参数自适应**：`text_recognition_batch_size`、`text_det_limit_side_len` 等参数根据系统资源动态计算

* **修复 render\_dpi 未消费**：profiler 计算的 render\_dpi 传入实际渲染代码

* **恢复 feature skipping**：极低内存时自动跳过表格/公式识别（基于总内存判断，避免动态波动误判）

* **修复 batch\_size 不一致**：统一 OCR\_BATCH\_SIZE 默认值

## Impact

* Affected code: `modules/ocr/system_profiler.py`、`modules/ocr/paddle_extractor.py`、`modules/ocr/ocr_worker.py`、`config.py`

* **BREAKING**：GPU 可用时 OCR 将使用 GPU（之前强制 CPU），需要确保 GPU 环境兼容

* 行为变更：极低内存系统自动降级模型和跳过部分功能

## ADDED Requirements

### Requirement: GPU 自适应

系统 SHALL 在 OCR 子进程中根据 GPU 可用性自动选择 GPU 或 CPU 推理。当 `config.OCR_USE_GPU=True` 且系统有可用 CUDA GPU 时，使用 GPU 推理；否则使用 CPU。

#### Scenario: 系统有 CUDA GPU 且启用 GPU

* **WHEN** 系统有可用 CUDA GPU 且 `OCR_USE_GPU=True`

* **THEN** OCR 子进程使用 GPU 推理

* **AND** 不强制设置 `CUDA_VISIBLE_DEVICES=-1` 和 `PADDLE_ONLY_CPU=1`

#### Scenario: 系统无 GPU 或禁用 GPU

* **WHEN** 系统无可用 GPU 或 `OCR_USE_GPU=False`

* **THEN** OCR 子进程使用 CPU 推理（当前行为）

#### Scenario: macOS 系统

* **WHEN** 运行在 macOS 上

* **THEN** 默认 `OCR_USE_GPU=False`，使用 CPU 推理

### Requirement: 模型大小自适应

系统 SHALL 根据内存分级选择不同大小的模型。高内存系统使用大模型（高精度），低内存系统使用小模型（低资源占用）。内存分级基于 `total_memory_gb`（总物理内存）判断，而非 `available_memory_gb`（可用内存），确保分级稳定不受运行时内存波动影响。

#### Scenario: 内存分级与模型选择

| 内存分级              | Layout 模型      | Formula 模型            | Text Det              | Text Rec              | Table        |
| ----------------- | -------------- | --------------------- | --------------------- | --------------------- | ------------ |
| minimal (≤8GB)    | PP-DocLayout-S | PP-FormulaNet\_plus-S | PP-OCRv4\_mobile\_det | PP-OCRv4\_mobile\_rec | SLANet       |
| low (8-16GB)      | PP-DocLayout-M | PP-FormulaNet\_plus-S | PP-OCRv4\_server\_det | PP-OCRv4\_server\_rec | SLANet\_plus |
| medium (16-32GB)  | PP-DocLayout-M | PP-FormulaNet\_plus-M | PP-OCRv4\_server\_det | PP-OCRv4\_server\_rec | SLANet\_plus |
| high (32-64GB)    | PP-DocLayout-L | PP-FormulaNet\_plus-M | PP-OCRv4\_server\_det | PP-OCRv4\_server\_rec | SLANet\_plus |
| unlimited (64GB+) | PP-DocLayout-L | PP-FormulaNet\_plus-L | PP-OCRv4\_server\_det | PP-OCRv4\_server\_rec | SLANet\_plus |

* **WHEN** 系统可用内存为 4GB（minimal 分级）

* **THEN** 使用 PP-DocLayout-M + PP-FormulaNet\_plus-S + mobile 检测/识别模型 + SLANet\_plus 表格模型

* **WHEN** 系统可用内存为 12GB（low 分级，如 16GB macOS 设备）

* **THEN** 使用 PP-DocLayout-S + PP-FormulaNet\_plus-S + mobile 检测/识别模型

* **AND** 表格和公式识别**不被跳过**

* **WHEN** 系统可用内存为 24GB（medium 分级）

* **THEN** 使用 PP-DocLayout-M + PP-FormulaNet\_plus-M + server 检测/识别模型

#### Scenario: GPU 模式下的模型选择

* **WHEN** GPU 可用且启用

* **THEN** 模型大小提升一级（GPU 显存补充系统内存）

### Requirement: 推理参数自适应

系统 SHALL 根据系统资源动态计算推理参数，而非硬编码固定值。

#### Scenario: text\_recognition\_batch\_size 自适应

| 内存分级           | batch\_size |
| -------------- | ----------- |
| minimal        | 4           |
| low            | 6           |
| medium         | 10          |
| high/unlimited | 16          |

* **WHEN** 系统为 minimal 分级

* **THEN** `text_recognition_batch_size=4`

#### Scenario: text\_det\_limit\_side\_len 自适应

| 内存分级           | side\_len |
| -------------- | --------- |
| minimal/low    | 720       |
| medium         | 960       |
| high/unlimited | 960       |

#### Scenario: GPU 模式下参数调整

* **WHEN** GPU 可用

* **THEN** `text_det_limit_side_len=960`（GPU 不受分辨率限制）

* **AND** `text_recognition_batch_size=16`

### Requirement: 修复 render\_dpi 未消费

系统 SHALL 将 profiler 计算的 `render_dpi` 传入页面渲染代码，替代 `config.OCR_RENDER_DPI` 的静态值。

#### Scenario: profiler 计算 render\_dpi

* **WHEN** profiler 根据内存分级计算 `render_dpi=100`（minimal）

* **THEN** 页面渲染使用 DPI=100

* **AND** 不使用 `config.OCR_RENDER_DPI` 的静态默认值

### Requirement: 恢复 feature skipping（基于总内存判断）

系统 SHALL 在极低内存时自动跳过表格和公式识别，恢复 `should_skip_table()` 和 `should_skip_formula()` 的条件逻辑。

**关键设计决策**：feature skipping 使用 `total_memory_gb`（总物理内存）而非 `available_memory_gb`（可用内存）作为判断依据。原因：

1. `available_memory_gb` 是动态值，运行时波动大，16GB 机器在高内存占用时可用内存可能跌至 7GB 以下
2. 使用总内存判断更稳定，反映机器的实际硬件能力
3. 确保中端设备（如 16GB macOS）在任何内存压力下都不会误跳过功能

#### Scenario: 公式识别跳过条件

* **WHEN** 系统总物理内存 ≤ 8GB（minimal 分级基于总内存）

* **THEN** `should_skip_formula()` 返回 `True`

* **AND** 公式识别被跳过

#### Scenario: 表格识别跳过条件

* **WHEN** 系统总物理内存 ≤ 4GB

* **THEN** `should_skip_table()` 返回 `True`

* **AND** 表格识别也被跳过

#### Scenario: 16GB macOS 设备（当前开发设备）

* **WHEN** 系统总物理内存为 16GB（low 分级）

* **THEN** `should_skip_formula()` 返回 `False`

* **AND** `should_skip_table()` 返回 `False`

* **AND** 表格和公式识别均正常执行

#### Scenario: 8GB 设备

* **WHEN** 系统总物理内存为 8GB（minimal 分级）

* **THEN** `should_skip_formula()` 返回 `True`（公式识别跳过）

* **AND** `should_skip_table()` 返回 `False`（表格识别仍执行）

#### Scenario: 4GB 及以下设备

* **WHEN** 系统总物理内存 ≤ 4GB

* **THEN** `should_skip_formula()` 返回 `True`

* **AND** `should_skip_table()` 返回 `True`

* **AND** 表格和公式识别均跳过

#### Scenario: medium 及以上分级

* **WHEN** 系统总物理内存 > 16GB（medium 分级或更高）

* **THEN** `should_skip_table()` 和 `should_skip_formula()` 均返回 `False`

### Requirement: 修复 OCR\_BATCH\_SIZE 不一致

系统 SHALL 统一 `OCR_BATCH_SIZE` 的默认值。`pdf_extractor.py` 中的 fallback 默认值应与 `config.py` 一致。

#### Scenario: OCR\_BATCH\_SIZE 默认值

* **WHEN** 未设置 `OCR_BATCH_SIZE` 环境变量

* **THEN** `config.py` 和 `pdf_extractor.py` 使用相同的默认值

## MODIFIED Requirements

### Requirement: OcrParameterCalculator 输出

`compute_all_params()` SHALL 额外返回模型名称和推理参数：`model_names`（layout、formula、text\_det、text\_rec、table）、`inference_params`（batch\_size、det\_limit\_side\_len）、`use_gpu`、`render_dpi`。

### Requirement: \_ocr\_worker\_func GPU 处理

从"强制 CPU 模式"改为"根据 profiler 结果选择 GPU/CPU"。

### Requirement: \_create\_pipeline 模型选择

从"固定模型名称"改为"从 ocr\_params 读取模型名称"。

### Requirement: should\_skip\_table / should\_skip\_formula 判断依据

从"基于 available\_memory\_gb"改为"基于 total\_memory\_gb"，避免运行时内存波动导致中端设备误跳过功能。

## REMOVED Requirements

（无移除的需求）
