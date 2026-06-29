# Tasks

- [x] Task 1: 为 `translate` 子命令添加 `--translation-model`、`--layout-model`、`--glossary-model`、`--ocr-llm-model` 四个参数定义
  - 在 `cli.py` 的 `translate_parser` 中添加四个可选参数
  - 每个参数默认值为 `None`
  - 为 `--ocr-llm-model` 添加 `dest='ocr_llm_model'` 避免与 `--ocr` 混淆

- [x] Task 2: 为 `glossary` 子命令添加 `--glossary-model` 参数定义
  - 在 `cli.py` 的 `glossary_parser` 中添加 `--glossary-model` 可选参数
  - 默认值为 `None`

- [x] Task 3: 修改 `cli/translate_command.py` 传递新模型参数
  - 在 `translate_handler()` 中将 `args.translation_model`、`args.layout_model`、`args.glossary_model`、`args.ocr_llm_model` 传递给 `process_translation_sync()`
  - 添加日志输出（verbose 模式下显示指定的模型名）

- [x] Task 4: 修改 `cli/glossary_command.py` 传递 `--glossary-model` 参数
  - 在 `glossary_handler()` 中将 `args.glossary_model` 传递给 `extract_glossary_sync()`

- [x] Task 5: 修改 `services/translation_service.py` 的 `process_translation_sync()` 接受并传递模型参数
  - 添加 `translation_model`、`layout_model`、`glossary_model`、`ocr_llm_model` 四个可选参数
  - 在调用 `get_translator()` 时传递 `translation_model`
  - 在调用 `get_semantic_analyzer()` 时传递 `translation_model`
  - 在调用 `_get_markdown_generator_config()` 时传递 `layout_model`
  - 在调用 OCR 提取或生成时传递 `ocr_llm_model`
  - 在调用 glossary 提取时传递 `glossary_model`

- [x] Task 6: 修改 `services/glossary_service.py` 接受并传递 glossary 模型参数
  - 修改 `extract_glossary_sync()` 添加 `glossary_model=None` 参数
  - 在调用 `create_glossary_extractor()` 时传递该参数

- [x] Task 7: 修改 `modules/glossary_extractor.py` 的工厂函数支持模型参数
  - 修改 `create_glossary_extractor()` 添加 `model=None` 参数
  - 创建 `AipingGlossaryExtractor(model=model)` 和 `SiliconFlowGlossaryExtractor(model=model)` 时传递

# Task Dependencies
- [Task 1, Task 2] 无依赖，可并行
- [Task 3] 依赖 [Task 1]
- [Task 4] 依赖 [Task 2]
- [Task 5] 依赖 [Task 3]
- [Task 6] 依赖 [Task 4]
- [Task 7] 依赖 [Task 6]
