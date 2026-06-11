# Intel Mac 16GB OCR 内存深度优化 验证清单

- [x] `ocr_worker.py` 在 paddle import 前设置了 `OMP_NUM_THREADS=2`、`MKL_NUM_THREADS=2`、`CUDA_VISIBLE_DEVICES=-1`
- [x] `ocr_worker.py` 在 paddle import 前设置了 `DNNL_VERBOSE=0`、`PADDLE_WITH_GPU=OFF` 等其他纯 CPU 强制变量（共11个环境变量）
- [x] `paddle_extractor.py` MEMORY_THRESHOLD_* 改为动态计算 `min(available * 0.55, cap)` 而非固定 2GB，上限分别降至1600/1600/1000MB
- [x] `config.py` 有新增 `OCR_SKIP_TABLE`, `OCR_SKIP_FORMULA`, `OCR_RENDER_DPI` 环境变量支持
- [x] `paddle_extractor.py` `_render_pages()` 接受从 config 读取的 `OCR_RENDER_DPI` 参数，用户可配置120激进优化
- [x] `paddle_extractor.py` `extract_from_pdf()` 检查 config.skip_table / skip_formula，为 True 直接跳过对应大步骤
- [x] （可选P2）页面数多时支持每 N 页销毁 pipeline 并 GC，减少碎片累积（本版未做，先验证前6项是否足够）
