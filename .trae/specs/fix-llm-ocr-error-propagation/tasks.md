# Tasks

- [ ] Task 1: 修复 `_extract_page` 异常时返回具体错误信息
  - 将通用 `except Exception` 中的 `return (None, None)` 改为 `return (None, f"LLM OCR API 请求失败: {str(e)}")`
  - 确保认证错误（401）、限流（429）、服务端错误（500）等都能被捕获并向上传递

# Task Dependencies

无（单文件单处修改）
