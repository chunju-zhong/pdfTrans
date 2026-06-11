- [x] 根因分析完成：确认 PaddleOCR 内部 ThreadPoolExecutor 并行预取导致文件访问竞态

- [x] `_process_page_layout` 在调用 `pipeline.predict()` 前读取图片到 numpy array

- [x] `_process_page_layout` 添加文件存在性检查作为防御性编程

- [x] `_process_page_tables` 同步使用 numpy array 输入

- [x] `_process_page_formulas` 同步使用 numpy array 输入

- [x] pytest tests/test_ocr_extractor.py 全部通过（56 passed）

- [ ] 手动测试超过15页 PDF 不再出现 FileNotFoundError