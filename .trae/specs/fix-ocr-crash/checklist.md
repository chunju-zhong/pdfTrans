# Checklist

- [x] config.py 中 OCR_USE_GPU 在 macOS 上默认为 False
- [x] paddle_extractor.py 中添加了 GPU 可用性检测
- [x] GPU 不可用时自动回退到 CPU 并记录警告日志
- [x] PaddleOCR 初始化异常被捕获并记录完整堆栈
- [x] 异常消息包含用户友好提示
- [x] 测试用例更新并通过
- [x] 在 macOS 上测试 OCR 功能正常运行（验证：`OCR_USE_GPU: False`，23个测试全部通过）
