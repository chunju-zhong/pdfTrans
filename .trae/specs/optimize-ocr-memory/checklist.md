# Checklist

- [x] OCR 子进程使用 `spawn` 上下文创建，避免 macOS 上的 fork 问题
- [x] OCR 子进程启动时设置 PaddlePaddle 环境变量（CPU_NUM=2 等）
- [x] `_create_pipeline()` 接受 `use_region_detection` 参数，默认为 `False`
- [x] 所有 `_create_pipeline()` 调用传递 `use_region_detection=False`
- [x] PDF 渲染 DPI 从 200 降低到 150
- [x] OCR 子进程每个步骤前后记录 RSS 内存使用量
- [x] 步骤2创建管线时禁用公式识别和区域检测
- [x] 步骤3创建管线时禁用表格识别和区域检测
- [ ] 在 16GB Mac 上测试：OCR 模式不触发段错误
