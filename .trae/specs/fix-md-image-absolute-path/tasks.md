# Tasks
- [x] Task 1: 删除 paddle_extractor.py 中的 temp_images 清理逻辑：移除 OCR 提取完成后对 temp_images 目录的清理代码，让临时图片保留到翻译服务层统一管理。
  - [x] 找到 `paddle_extractor.py` 中清理 `temp_images_dir` 的代码块（约第1165-1172行）
  - [x] 删除该清理代码块（`shutil.rmtree(temp_images_dir, ...)`）
  - [x] 确认删除了相关的 `import shutil`（其他地方不再使用，已一并移除）

- [x] Task 2: 在翻译服务层添加 temp_images 统一清理：在 `translation_service.py` 中确保所有输出文件生成完成后才清理 temp_images 目录。
  - [x] 分析 `process_translation()` 和 `_generate_outputs()` 流程，确定合适的清理时机
  - [x] 添加清理 `temp_images/` 目录的逻辑（在 `_complete_task()` 之后或在 `generate_output_files()` 之后）
  - [x] 确保多格式输出（pdf + docx + md）时，所有输出生成完成后再清理
  - [x] 添加 `_cleanup_ocr_temp_images()` 方法，从图片路径推导临时目录
  - [x] 在 `process_translation()` 和 `process_translation_sync()` 的成功与异常路径都添加了清理

- [ ] Task 3: 验证修复效果：检查生成的 markdown 文件中图片路径是否为相对路径，以及在 ZIP 包中是否能正常显示。
  - [x] 语法检查通过（python3 py_compile）
  - [x] 相关测试通过（27/27 markdown 相关测试，338 tests passed）
  - [ ] 检查生成 MD 中图片引用为 `images_{unique_id}/xxx.png` 格式（需实际OCR翻译运行验证）
  - [ ] 检查 `images_{unique_id}` 目录是否存在且包含图片文件（需实际OCR翻译运行验证）
  - [ ] 检查 ZIP 包中 MD 和图片的相对路径是否正确（需实际OCR翻译运行验证）

# Task Dependencies
- [Task 1] → [Task 2]: 必须先删除 OCR 提取器中的清理逻辑，才能在服务层统一管理
- [Task 2] → [Task 3]: 验证需要在修复完成后进行
