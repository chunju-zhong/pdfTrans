# Checklist

- [x] `translate` 子命令有 `--translation-model` 参数，类型为 str，默认值为 None
- [x] `translate` 子命令有 `--layout-model` 参数，类型为 str，默认值为 None
- [x] `translate` 子命令有 `--glossary-model` 参数，类型为 str，默认值为 None
- [x] `translate` 子命令有 `--ocr-llm-model` 参数，类型为 str，默认值为 None
- [x] `glossary` 子命令有 `--glossary-model` 参数，类型为 str，默认值为 None
- [x] 指定 `--translation-model` 时，翻译器使用该模型而非默认配置
- [x] 指定 `--layout-model` 时，Markdown 排版使用该模型而非默认配置
- [x] 指定 `--glossary-model` 时，术语提取使用该模型而非默认配置
- [x] 指定 `--ocr-llm-model` 时，LLM OCR 使用该模型而非默认配置
- [x] 不传递任何 `--*-model` 参数时，行为与修改前完全一致（回归保护）
- [x] 参数仅在当前命令有效，不修改 `.env` 文件
