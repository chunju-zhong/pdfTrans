# Tasks

- [x] Task 1: 增大 MAX_CONTENT_LENGTH 上传限制
  - [x] SubTask 1.1: 将 config.py 中 MAX_CONTENT_LENGTH 从 50MB 改为 500MB
- [x] Task 2: 注册 Flask 413 错误处理器
  - [x] SubTask 2.1: 在 app.py 中添加 @app.errorhandler(413) 处理器，返回 JSON 格式响应
- [x] Task 3: 前端添加文件大小校验和 413 处理
  - [x] SubTask 3.1: 在 main.js 的 getPdfPageCount 函数中添加文件大小校验（上传前检查）
  - [x] SubTask 3.2: 在 main.js 的 getPdfPageCount 函数中添加 413 状态码专门处理
  - [x] SubTask 3.3: 在 main.js 的翻译提交逻辑中添加文件大小校验和 413 处理

# Task Dependencies
- Task 2 依赖 Task 1（错误处理器消息需引用新的大小限制值）
- Task 3 依赖 Task 1（前端校验需与后端限制一致）
