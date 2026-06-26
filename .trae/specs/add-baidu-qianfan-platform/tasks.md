# Tasks

- [x] Task 1: 配置层 — 在 `config.py` 和 `.env.example` 中添加百度千帆平台的配置项
  - `config.py`: 新增 `QIANFAN_API_KEY`, `QIANFAN_API_URL`, `QIANFAN_MODEL`, `QIANFAN_MODEL_LAYOUT`, `QIANFAN_MODEL_GLOSSARY`, `QIANFAN_EXTRA_BODY`, `QIANFAN_OCR_LLM_MODEL`
  - `.env.example`: 新增对应的环境变量模板
- [x] Task 2: 翻译器 — 新建 `modules/qianfan_translator.py`，继承 `Translator` 基类
  - 参考 `SiliconFlowTranslator` 实现，使用非流式调用、`OpenAI` 客户端
  - 支持 `translate()` 和 `batch_translate()` 方法
  - 支持错误处理和截断检测
- [x] Task 3: 分派点集成 — 在多个分派点添加 `qianfan` 分支
  - `services/translation_service.py`:
    - `get_translator()` 新增 `'qianfan'` 分支
    - `get_semantic_analyzer()` 新增 `'qianfan'` 分支
    - `_get_markdown_generator_config()` 新增 `'qianfan'` 分支
  - `modules/semantic_analyzer_factory.py`:
    - `create_analyzer()` 新增 `'qianfan'` 分支（复用基类 `SemanticAnalyzer`）
    - `get_available_analyzers()` 新增 `'qianfan'`
  - `modules/glossary_extractor.py`:
    - `create_glossary_extractor()` 新增 `'qianfan'` 分支
    - 新建 `QianfanGlossaryExtractor` 类（参考 `SiliconFlowGlossaryExtractor`）
  - `modules/ocr/llm_extractor.py`:
    - `client` property 新增 `'qianfan'` 分支
- [x] Task 4: 用户界面 — 在 CLI 和 Web 界面添加百度千帆选项
  - `cli.py`: translate 和 glossary 子命令的 `--translator` 参数 `choices` 新增 `'qianfan'`
  - `templates/index.html`: 翻译服务下拉框新增 `<option value="qianfan">百度千帆翻译</option>`
- [x] Task 5: 测试 — 创建 `tests/test_qianfan_translator.py`
  - 继承自 `test_silicon_flow_translator.py` 的测试结构
  - 测试翻译器初始化、翻译调用、语言一致、错误处理

## Task Dependencies

- Task 2 依赖 Task 1（翻译器需要配置项支持）
- Task 3 依赖 Task 1 和 Task 2（分派点需要配置项和翻译器类）
- Task 4 依赖 Task 3（UI 选项需要后端支持）
- Task 5 可与其他任务并行
