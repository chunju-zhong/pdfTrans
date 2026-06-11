# Tasks

- [x] Task 1: 修复 config.py 中 OCR_USE_GPU 默认值
  - [x] SubTask 1.1: 导入 platform 模块
  - [x] SubTask 1.2: 检测操作系统，macOS 上默认使用 CPU
  - [ ] SubTask 1.3: 更新 .env.example 文档说明

- [x] Task 2: 在 paddle_extractor.py 中添加 GPU 可用性检测
  - [x] SubTask 2.1: 添加 _check_gpu_available() 方法
  - [x] SubTask 2.2: 在 pipeline 属性初始化前检测 GPU
  - [x] SubTask 2.3: GPU 不可用时自动回退到 CPU 并记录警告

- [x] Task 3: 增强 PaddleOCR 初始化异常处理
  - [x] SubTask 3.1: 在 pipeline 属性中添加 try-except
  - [x] SubTask 3.2: 捕获所有异常并记录完整堆栈
  - [x] SubTask 3.3: 抛出包含用户友好提示的异常

- [x] Task 4: 更新测试用例
  - [x] SubTask 4.1: 更新 test_ocr_config 测试默认值
  - [x] SubTask 4.2: 添加 GPU 自动回退测试

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 1, Task 2, Task 3]
