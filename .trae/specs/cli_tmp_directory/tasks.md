# CLI临时目录管理 Tasks

## [ ] Task 1: 修改 translate_command.py 创建 tmp 目录
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 在 `translate_handler` 函数中，当处理 `-o` 参数时，在输出目录下创建 `tmp` 子目录
  - 将 `tmp` 目录路径传递给 `process_translation_sync` 方法
  - 确保目录创建失败时有适当的错误处理
- **Test Requirements**:
  - `programmatic`: 验证 `tmp` 目录在指定输出目录下被正确创建
  - `programmatic`: 验证未指定 `-o` 时在默认 `outputs` 目录下创建 `tmp`

## [ ] Task 2: 修改 translation_service.py 使用 tmp 目录
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 修改 `process_translation_sync` 方法接受 `tmp_dir` 参数
  - 修改 `extract_pdf_content` 方法将图像提取到 `tmp` 目录
  - 修改所有输出生成方法，先生成到 `tmp` 目录
  - 添加最终文件移动逻辑，将结果从 `tmp` 移动到最终位置
- **Test Requirements**:
  - `programmatic`: 验证图像被提取到 `tmp` 目录
  - `programmatic`: 验证中间文件存放在 `tmp` 目录
  - `programmatic`: 验证最终结果正确移动到指定位置

## [ ] Task 3: 修改 pdf_extractor.py 支持 tmp 目录
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 确保 `extract` 方法正确接收和使用 `temp_images_dir` 参数
  - 验证图像被保存到指定的 `tmp` 目录
- **Test Requirements**:
  - `programmatic`: 验证图像提取到正确的 `tmp` 目录位置

## [ ] Task 4: 修改 glossary_command.py 和 glossary_service.py
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 在 `glossary_handler` 函数中创建 `tmp` 子目录
  - 修改 `glossary_service.extract_glossary_sync` 方法接受 `tmp_dir` 参数
  - 将术语提取过程中的临时文件存放到 `tmp` 目录
- **Test Requirements**:
  - `programmatic`: 验证术语提取时 tmp 目录被正确创建
  - `programmatic`: 验证临时文件存放在 tmp 目录
  - `programmatic`: 验证最终术语表保存到指定位置

## [ ] Task 5: 测试各种场景
- **Priority**: P1
- **Depends On**: Tasks 1, 2, 3, 4
- **Description**:
  - 测试指定 `-o` 目录时的 tmp 目录创建
  - 测试未指定 `-o` 时的默认行为
  - 测试 `tmp` 目录已存在的情况
  - 测试多格式输出（PDF、DOCX、Markdown）
  - 测试术语提取命令的 tmp 目录管理
- **Test Requirements**:
  - `programmatic`: 所有场景下 tmp 目录管理正常工作
  - `programmatic`: 最终结果正确放置在指定位置

## [ ] Task 6: 更新文档
- **Priority**: P2
- **Depends On**: Tasks 1, 2, 3, 4, 5
- **Description**:
  - 检查并更新相关文档，说明 tmp 目录的使用
  - 更新 README 中的命令行使用说明
- **Test Requirements**:
  - `human-judgment`: 文档准确反映新行为
