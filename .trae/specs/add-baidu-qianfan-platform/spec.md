# 添加百度千帆平台支持 Spec

## Why

目前项目已支持 aiping 和硅基流动两个 AI 平台。增加百度千帆平台（百度智能云千帆大模型平台）的支持，为用户提供更多翻译服务选择。百度千帆平台提供 OpenAI 兼容 API，可以复用现有的调用模式。

## What Changes

- 在 `config.py` 中新增 `QIANFAN_*` 系列配置项（API Key / URL / 翻译模型 / 排版模型 / 术语模型 / EXTRA_BODY / OCR LLM 模型）
- 在 `.env.example` 中新增百度千帆平台的环境变量模板
- 新建 `modules/qianfan_translator.py` — 继承 `Translator` 基类，非流式调用
- 在 `modules/semantic_analyzer_factory.py` 中新增 `qianfan` 分支（复用基类 `SemanticAnalyzer`）
- 在 `services/translation_service.py` 的 `get_translator()`、`get_semantic_analyzer()`、`_get_markdown_generator_config()` 中新增 `qianfan` 分支
- 在 `modules/glossary_extractor.py` 的 `create_glossary_extractor()` 中新增 `qianfan` 分支
- 在 `modules/ocr/llm_extractor.py` 的 `client` property 中新增 `qianfan` 分支，读取 `QIANFAN_API_KEY/URL/OCR_MODEL`
- 在 `cli.py` 的 translate 和 glossary 子命令的 `--translator` 参数 choices 中新增 `qianfan`
- 在 `templates/index.html` 的翻译服务选择下拉框中新增百度千帆选项
- 新增 `modules/qianfan_semantic_analyzer.py`（可选，如无特殊参数需求可直接复用基类）
- 更新 `tests/` 目录下的对应测试文件

## Impact

- Affected specs: 翻译服务选择、配置管理
- Affected code:
  - `config.py` — 配置项
  - `.env.example` — 环境变量模板
  - `modules/qianfan_translator.py` — **新建** 翻译器
  - `modules/semantic_analyzer_factory.py` — 工厂分支
  - `services/translation_service.py` — 服务层分派
  - `modules/glossary_extractor.py` — 术语提取工厂
  - `modules/ocr/llm_extractor.py` — LLM OCR 分支
  - `cli.py` — CLI 参数 choices
  - `templates/index.html` — 前端选择框
  - `tests/test_qianfan_translator.py` — **新建** 测试

## ADDED Requirements

### Requirement: 百度千帆平台配置

系统 SHALL 支持通过环境变量配置百度千帆平台的 API 参数。

#### Scenario: 配置读取
- **WHEN** 环境变量 `QIANFAN_API_KEY`、`QIANFAN_API_URL`、`QIANFAN_MODEL_TRANSLATION`、`QIANFAN_MODEL_LAYOUT`、`QIANFAN_MODEL_GLOSSARY`、`QIANFAN_OCR_LLM_MODEL` 已设置
- **THEN** `config.QIANFAN_API_KEY` 等属性 SHALL 返回对应的值
- **AND** 默认值 SHALL 为：`QIANFAN_API_URL=https://qianfan.baidubce.com/v2`，翻译模型 `Qwen3-32B`，排版模型 `Qwen3-32B`，术语模型 `Qwen3-32B`

#### Scenario: 配置缺失
- **WHEN** 用户选择 qianfan 平台但 `QIANFAN_API_KEY` 未设置
- **THEN** SHALL 抛出 `ValueError` 提示"百度千帆API配置不完整"

### Requirement: 百度千帆翻译器

系统 SHALL 提供 `QianfanTranslator` 类，继承 `Translator`，实现百度千帆平台的翻译调用。

#### Scenario: 初始化
- **WHEN** 创建 `QianfanTranslator(api_key, api_url, model)` 实例
- **THEN** SHALL 使用 `OpenAI` 客户端连接 `api_url`
- **AND** 设置 `max_tokens = 8192`

#### Scenario: 翻译调用
- **WHEN** 调用 `translate(text, source_lang, target_lang, doc_type, glossary)`
- **THEN** SHALL 使用非流式 (`stream=False`) 调用 OpenAI Chat API
- **AND** 设置 `temperature=0.1`, `top_p=0.9`
- **AND** SHALL 返回 `TranslationResult` 对象
- **AND** SHALL 捕获 token 用量信息和 finish_reason
- **AND** SHALL 检查截断 (`finish_reason == "length"`)

#### Scenario: 错误处理
- **WHEN** API 请求失败
- **THEN** SHALL 抛出 `Exception("百度千帆翻译API请求失败: {str(e)}")`

#### Scenario: 批量翻译
- **WHEN** 调用 `batch_translate()`
- **THEN** SHALL 逐条调用 `translate()` 并返回结果列表

#### Scenario: 语言一致
- **WHEN** `source_lang == target_lang`
- **THEN** SHALL 直接返回原文本

### Requirement: 百度千帆平台分派

系统 SHALL 在各分派点支持 `qianfan` 类型。

#### Scenario: 翻译器创建
- **WHEN** `translation_service.get_translator('qianfan')` 被调用
- **THEN** SHALL 返回 `QianfanTranslator` 实例，使用 `config.QIANFAN_API_KEY/URL/MODEL`

#### Scenario: 语义分析器创建
- **WHEN** `translation_service.get_semantic_analyzer('qianfan')` 被调用
- **THEN** SHALL 通过 `SemanticAnalyzerFactory.create_analyzer('qianfan', ...)` 创建标准 `SemanticAnalyzer` 实例

#### Scenario: Markdown排版配置
- **WHEN** `_get_markdown_generator_config('qianfan')` 被调用
- **THEN** SHALL 返回 `config.QIANFAN_API_KEY`, `config.QIANFAN_API_URL`, `config.QIANFAN_MODEL_LAYOUT`

#### Scenario: 术语提取器创建
- **WHEN** `create_glossary_extractor('qianfan')` 被调用
- **THEN** SHALL 返回 `QianfanGlossaryExtractor` 实例

#### Scenario: LLM OCR 客户端
- **WHEN** LLM OCR 提取器的 `translator_type` 为 `'qianfan'`
- **THEN** SHALL 使用 `config.QIANFAN_API_KEY/URL` 和 `config.QIANFAN_OCR_LLM_MODEL`

### Requirement: 用户界面

系统 SHALL 在 CLI 和 Web 界面提供百度千帆平台选项。

#### Scenario: CLI 参数
- **WHEN** 执行 `pdftrans translate --translator qianfan`
- **THEN** SHALL 识别 `qianfan` 为有效选项

#### Scenario: Web 选择框
- **WHEN** 用户打开 Web 界面
- **THEN** 翻译服务下拉框 SHALL 包含 `百度千帆翻译` 选项，值为 `qianfan`
