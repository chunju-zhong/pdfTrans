# Intel Mac 16GB OCR 内存深度优化 — The Implementation Plan (Decomposed and Prioritized Task List)

## [x] Task 1: ocr_worker.py 添加 MKL/DNN/Intel 纯 CPU 环境变量
- **Priority**: P0
- **Depends On**: 无
- **Description**: 
  - ✅ Done: 在 `_ocr_worker_func()` paddle import 之前添加了11个强制纯 CPU 环境变量
  - `FLAGS_fraction_of_gpu_memory_to_use=0.5`, `CPU_NUM=2`
  - `OMP_NUM_THREADS=2`, `MKL_NUM_THREADS=2`
  - `CUDA_VISIBLE_DEVICES=-1` (强制无 CUDA)
  - `DNNL_VERBOSE=0`, `PADDLE_WITH_GPU=OFF`, `PADDLE_ONLY_CPU=1`
  - `KMP_AFFINITY=disabled`, `KMP_DUPLICATE_LIB_OK=TRUE`
  - `MKL_THREADING_LAYER=sequential`, `OPENBLAS_NUM_THREADS=2`

## [x] Task 2: paddle_extractor.py 动态内存阈值 + 激进 GC 选项
- **Priority**: P0
- **Depends On**: 无
- **Description**: 
  - ✅ Done: 内存阈值类改为 `min(available*0.55, cap)` 动态计算
  - `MEMORY_FACTOR = 0.55` (原固定 2GB)
  - 上限: 版面/表格 1600MB, 公式 1000MB
  - 代码先 `available = _check_available_memory()` 再按 factor 动态计算阈值

## [x] Task 3: config.py 添加 `OCR_SKIP_TABLE`, `OCR_SKIP_FORMULA`, `OCR_RENDER_DPI` env var
- **Priority**: P1
- **Depends On**: 无
- **Description**: 
  - ✅ Done: 在 `config.py` 中新增三个环境变量
  - `OCR_SKIP_TABLE=False` 默认: 跳过表格识别节省内存
  - `OCR_SKIP_FORMULA=False` 默认: 跳过公式识别节省内存
  - `OCR_RENDER_DPI=150` 默认: 120=激进内存优化

## [x] Task 4: paddle_extractor.py 接入新增 config 并适配分步跳过逻辑
- **Priority**: P1
- **Depends On**: Task 3
- **Description**: 
  - ✅ Done: `from config import config` 导入配置
  - ✅ Done: `_render_pages()` 打印日志并读取 `config.OCR_RENDER_DPI`
  - ✅ Done: `extract_from_pdf()` 开头打印全部 OCR 优化配置值
  - ✅ Done: 步骤2 检查 `config.OCR_SKIP_TABLE` 为 True 时直接空字典跳过
  - ✅ Done: 步骤3 检查 `config.OCR_SKIP_FORMULA` 为 True 时直接空字典跳过

## [ ] Task 5 (可选优化): paddle_extractor.py 页面粒度管线重建而非整批处理完再销毁
- **Priority**: P2
- **Depends On**: Task 2
- **Description**: 
  - 本版暂不实施，先验证 Task1-4 是否足够解决问题
  - 超长篇文档后半部分内存碎片确有问题再考虑每 N 页销毁重建

## Task Dependencies
- Task 4 depends on Task 3
- Task 5 depends on Task 2
