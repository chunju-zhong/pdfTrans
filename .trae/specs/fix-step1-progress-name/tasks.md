# Tasks

- [x] Task 1: 在 PaddleOcrExtractor 类中定义步骤常量
  - [x] SubTask 1.1: 在类定义中添加步骤常量：STEP_LAYOUT_OCR=1, STEP_LAYOUT_OCR_NAME='版面分析+文本+公式+表格', STEP_IMAGE_CROP=2, STEP_IMAGE_CROP_NAME='图像裁剪'

- [x] Task 2: 替换 paddle_extractor.py 中所有硬编码的步骤编号和名称为常量引用
  - [x] SubTask 2.1: 替换内存检查中的 step_name 为常量引用
  - [x] SubTask 2.2: 替换 step_start 回调中的 step 和 step_name 为常量引用
  - [x] SubTask 2.3: 替换 step_progress 回调中的 step 为常量引用
  - [x] SubTask 2.4: 替换 step_complete 回调中的 step 和 step_name 为常量引用
  - [x] SubTask 2.5: 替换日志消息中的硬编码步骤名称为常量引用
  - [x] SubTask 2.6: 替换步骤 2 的 step_start 回调中的 step 和 step_name 为常量引用
  - [x] SubTask 2.7: 替换步骤 2 的 step_complete 回调中的 step 和 step_name 为常量引用

- [x] Task 3: 替换 translation_service.py 中 STEP_WEIGHTS 的硬编码键为常量引用
  - [x] SubTask 3.1: 导入 PaddleOcrExtractor
  - [x] SubTask 3.2: 将 STEP_WEIGHTS 从 {1: 0.80, 2: 0.20} 改为 {PaddleOcrExtractor.STEP_LAYOUT_OCR: 0.80, PaddleOcrExtractor.STEP_IMAGE_CROP: 0.20}

# Task Dependencies
- Task 2 依赖 Task 1
- Task 3 依赖 Task 1
