# Tasks

- [x] Task 1: 修复参数传递链路
  - [x] SubTask 1.1: 修复 translation_service.py `extract_pdf_content` 调用未传递 `extract_chapter=chapter_split`（第1399-1402行和第1659-1662行）

- [x] Task 2: 清理 OCR 功能开关配置
  - [x] SubTask 2.1: 从 config.py 移除 `OCR_USE_TABLE_RECOGNITION` 和 `OCR_USE_FORMULA_RECOGNITION`
  - [x] SubTask 2.2: 从 pdf_extractor.py 的 `ocr_extractor` 属性移除功能开关参数传递
  - [x] SubTask 2.3: 从 PaddleOcrExtractor.__init__ 移除 `use_table_recognition`、`use_formula_recognition`、`use_seal_recognition`、`use_chart_recognition` 参数
  - [x] SubTask 2.4: 从 factory.py 的 create_ocr_extractor 移除相关参数

- [x] Task 3: 重构 PaddleOcrExtractor 为分步骤提取
  - [x] SubTask 3.1: 新增 `_extract_original_images()` 方法：使用 PyMuPDF 直接提取 PDF 嵌入的原始图片
  - [x] SubTask 3.2: 新增 `_create_pipeline()` 方法：根据参数创建不同配置的 PPStructureV3 实例
  - [x] SubTask 3.3: 新增 `_process_page_layout()` 方法：版面分析+文本OCR，返回文本块和各区域边界框
  - [x] SubTask 3.4: 新增 `_process_page_tables()` 方法：仅加载表格模型，处理有表格区域的页面
  - [x] SubTask 3.5: 新增 `_process_page_formulas()` 方法：仅加载公式模型，处理有公式区域的页面
  - [x] SubTask 3.6: 重构 `extract_from_pdf()` 方法：按步骤调用，每步完成后 `del pipeline; gc.collect()`
  - [x] SubTask 3.7: 移除 `self._local` threading.local 管线缓存（不再复用管线实例）
  - [x] SubTask 3.8: 图表/印章区域直接从步骤1的版面分析结果裁剪保存，无需额外模型

- [x] Task 4: 内存预检机制
  - [x] SubTask 4.1: 在 `paddle_extractor.py` 中添加 `_check_available_memory()` 方法，使用 `psutil` 检测可用内存
  - [x] SubTask 4.2: 在每个步骤加载模型前调用内存预检：步骤1需>=2GB，步骤2需>=2GB，步骤3需>=1GB
  - [x] SubTask 4.3: 内存不足时跳过当前步骤，记录警告，内容降级处理（如表格保存为图片）
  - [x] SubTask 4.4: 在 `requirements.txt` 中添加 `psutil` 依赖

- [x] Task 5: OCR 进程隔离
  - [x] SubTask 5.1: 创建 `modules/ocr/ocr_worker.py`，使用 `multiprocessing.Process` 在子进程中运行 OCR 提取
  - [x] SubTask 5.2: 实现主进程与子进程间的结果传递（通过 `multiprocessing.Queue` + to_dict/from_dict 序列化）
  - [x] SubTask 5.3: 在子进程崩溃时捕获异常（通过 `Process.exitcode` 检测），更新任务状态为错误
  - [x] SubTask 5.4: 修改 `pdf_extractor.py` 的 OCR 调用，通过 `run_ocr_in_subprocess()` 执行
  - [x] SubTask 5.5: 确保 OCR 子进程退出后释放所有模型内存和 IPC 资源

# Task Dependencies

- [Task 3] depends on [Task 2]（先清理旧的功能开关参数，再重构为分步骤提取）
- [Task 4] depends on [Task 3]（内存阈值需根据分步骤的模型加载量调整）
- [Task 5] depends on [Task 3]（进程隔离需在分步骤提取架构确定后实现）
