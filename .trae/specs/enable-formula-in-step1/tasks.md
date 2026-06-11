# Tasks

- [x] Task 1: 步骤1管线创建时启用公式识别
  - [x] SubTask 1.1: 将 `paddle_extractor.py` 步骤1的 `_create_pipeline(use_table=False, use_formula=False, ...)` 改为 `_create_pipeline(use_table=False, use_formula=True, ...)`
  - [x] SubTask 1.2: 在步骤1的 `_create_pipeline` 调用前添加内存检查，若可用内存不足以加载公式模型则回退到 `use_formula=False` 并记录警告

- [x] Task 2: 步骤1处理公式识别结果
  - [x] SubTask 2.1: 在 `_process_page_layout` 中，当管线启用公式识别时，从 `result["formula_res_list"]` 提取 LaTeX 公式，生成 `is_formula=True` 的 TextBlock 并加入 `text_blocks` 列表
  - [x] SubTask 2.2: 确保 `formula`/`formula_number` 标签的块不再被忽略，而是正确生成公式 TextBlock（与步骤3逻辑一致）

- [x] Task 3: 移除步骤3公式识别
  - [x] SubTask 3.1: 删除 `extract_from_pdf` 中步骤3的全部代码（公式识别逐页管线循环）
  - [x] SubTask 3.2: 删除步骤3相关的 `formula_blocks` 列表和合并逻辑
  - [x] SubTask 3.3: 删除 `_process_page_formulas` 方法（不再需要）
  - [x] SubTask 3.4: 更新步骤编号（原步骤4图表裁剪变为步骤3）

- [x] Task 4: 内存上限调整
  - [x] SubTask 4.1: 将 `MEMORY_CAP_LAYOUT` 从 1600MB 调整为 1800MB
  - [x] SubTask 4.2: 在 `system_profiler.py` 中对应调整 `cap_layout` 值

- [x] Task 5: 清理分批处理中的公式跳过逻辑
  - [x] SubTask 5.1: 移除 `pdf_extractor.py` 中的 `_low_memory_skip_formula` 逻辑（步骤3已不存在）
  - [x] SubTask 5.2: 移除 `ocr_worker.py` 中 `skip_formula` 参数的传递逻辑

- [x] Task 6: 验证
  - [x] SubTask 6.1: 语法检查通过（所有4个文件 py_compile OK）
  - [x] SubTask 6.2: 确认步骤3不再执行（代码已移除）
  - [x] SubTask 6.3: 确认内存不足时能优雅降级（try/except MemoryError 回退到 use_formula=False）

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 5 depends on Task 3
- Task 6 depends on Task 1, 2, 3, 4, 5
