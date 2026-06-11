# Tasks

- [x] Task 1: 根因分析已完成
  - [x] SubTask 1.1: 确认 PaddleOCR 内部使用 ThreadPoolExecutor 并行预取 batch
  - [x] SubTask 1.2: 确认 img_reader 在预取阶段尝试读取文件路径
  - [x] SubTask 1.3: 确认根因是并行预取导致文件访问竞态

- [x] Task 2: 修改 `_process_page_layout` 传递 numpy array 而非文件路径
  - [x] SubTask 2.1: 在调用 `pipeline.predict()` 前使用 cv2.imread() 读取图片到内存
  - [x] SubTask 2.2: 添加文件存在性检查，若不存在则记录错误并返回空结果
  - [x] SubTask 2.3: 修改 `pipeline.predict(img_path)` 为 `pipeline.predict(img_array)`

- [x] Task 3: 同步修改 `_process_page_tables` 和 `_process_page_formulas`
  - [x] SubTask 3.1: 在表格识别步骤中也使用 numpy array 输入
  - [x] SubTask 3.2: 在公式识别步骤中也使用 numpy array 输入

- [x] Task 4: 运行测试验证修复
  - [x] SubTask 4.1: 运行 pytest tests/test_ocr_extractor.py 确保现有测试通过
  - [x] SubTask 4.2: 手动测试处理超过15页的 PDF 确认不再出现 FileNotFoundError

# Task Dependencies

- Task 2 无依赖，可直接开始
- Task 3 依赖于 Task 2 的模式确定
- Task 4 依赖于 Task 2 和 Task 3 完成