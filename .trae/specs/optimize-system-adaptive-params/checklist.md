# Checklist

## OcrParameterCalculator 扩展

- [x] `compute_model_names()` 根据内存分级返回模型名称映射
- [x] `compute_inference_params()` 根据内存分级返回推理参数
- [x] `compute_all_params()` 包含 `model_names`、`inference_params`、`use_gpu`、`render_dpi`
- [x] `should_skip_formula()` 基于 `total_memory_gb` 判断，total ≤ 8GB 时返回 True
- [x] `should_skip_table()` 基于 `total_memory_gb` 判断，total ≤ 4GB 时返回 True
- [x] 16GB macOS 设备（low 分级）不跳过表格和公式识别

## GPU 自适应

- [x] `use_gpu=True` 时 OCR 子进程使用 GPU
- [x] `use_gpu=False` 时 OCR 子进程使用 CPU（保持当前行为）
- [x] macOS 默认 `use_gpu=False`
- [x] GPU 环境变量不再无条件强制 CPU

## 模型名称自适应

- [x] `_create_pipeline()` 从 `self.model_names` 读取模型名称
- [x] minimal 分级使用小模型（PP-DocLayout-S、mobile det/rec、SLANet）
- [x] low 分级使用中模型（PP-DocLayout-M、mobile det/rec、SLANet_plus）
- [x] medium/high/unlimited 分级使用大模型（PP-DocLayout-M/L、server det/rec）
- [x] formula 模型名称不再硬编码

## 推理参数自适应

- [x] `text_recognition_batch_size` 根据内存分级动态设置
- [x] `text_det_limit_side_len` 根据内存分级动态设置
- [x] GPU 模式下参数自动提升

## render_dpi 修复

- [x] `_render_pages()` 使用 profiler 的 render_dpi
- [x] 不再依赖 config.OCR_RENDER_DPI 静态值

## OCR_BATCH_SIZE 修复

- [x] pdf_extractor.py 的 fallback 默认值与 config.py 一致

## 端到端验证

- [x] 16GB macOS 设备：表格和公式识别均正常执行（不跳过）
- [x] 8GB 设备：公式识别跳过，表格识别正常
- [x] 4GB 及以下设备：表格和公式识别均跳过
- [x] GPU 系统正确使用 GPU 推理
- [x] macOS CPU 模式正常工作
