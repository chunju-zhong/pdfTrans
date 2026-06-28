# pdfTrans 项目架构文档

## 1. 项目定位与核心功能

pdfTrans 是一个 PDF 翻译工具，支持 **Web 界面**、**命令行（CLI）** 和 **AI IDE Skill** 三种调用方式。

### 核心能力

| 能力 | 说明 |
|------|------|
| PDF 文本提取 | 基于 PyMuPDF 提取文本块、表格、图像及样式信息 |
| OCR 文字识别 | 支持 PaddleOCR（PP-StructureV3 本地引擎）和 LLM OCR（DeepSeek-OCR 云端引擎） |
| 多翻译 API 翻译 | 支持 aiping（OpenAI 兼容 API）、硅基流动 SiliconFlow（OpenAI 兼容 API）和百度千帆 Qianfan（OpenAI 兼容 API） |
| 多格式输出 | PDF（保留原始排版）、DOCX（Word 文档）、Markdown（含章节拆分） |
| 术语表提取 | 从 PDF 中自动提取专业术语及翻译对照表 |
| 语义合并 | 规则合并或 LLM 语义判断合并，减少翻译碎片化 |
| 章节识别 | 自动识别文档章节结构，支持按章节拆分输出 |

### 支持的语言（9 种互译）

| 代码 | 语言 | 代码 | 语言 |
|------|------|------|------|
| zh | 中文 | en | 英语 |
| ja | 日语 | ko | 韩语 |
| fr | 法语 | de | 德语 |
| es | 西班牙语 | ru | 俄语 |
| bo | 藏文 | | |

---

## 2. 目录结构

```
pdfTrans/
├── app.py                          # Flask Web 入口，提供翻译和术语提取的 HTTP API
├── cli.py                          # CLI 入口，argparse 子命令路由
├── config.py                       # 配置类，从 .env 加载所有环境变量
├── SKILL.md                        # AI IDE Skill 定义文件（Claude Code / Trae 等）
├── .env.example                    # 环境变量模板
│
├── models/                         # 数据模型层
│   ├── copyable.py                 # CopyableMixin 基类，提供 copy() 和序列化
│   ├── text_block.py               # TextBlock — PDF 文本块模型
│   ├── extraction.py               # PdfPage / PdfCell / PdfTable / PdfImage / PdfExtraction — 提取结果模型
│   ├── merged_block.py             # MergedBlock — 语义合并后的块模型
│   ├── task.py                     # Task — 异步任务模型（含状态、进度、锁）
│   ├── phase_config.py             # PHASE_CONFIG / GLOSSARY_PHASE_CONFIG — 阶段进度配置
│   └── result_types.py             # TruncationInfo / Result / OpenAIResult / TranslationResult / MarkdownResult / MarkdownGenerationResult
│
├── modules/                        # 核心模块层
│   ├── pdf_extractor.py            # PdfExtractor — PDF 文本/表格/图像提取（PyMuPDF）
│   ├── pdf_generator.py            # PdfGenerator — 生成翻译后的 PDF
│   ├── docx_generator.py           # DocxGenerator — 生成翻译后的 Word 文档
│   ├── markdown_generator.py       # MarkdownGenerator — 生成翻译后的 Markdown（含 LLM 排版）
│   ├── translator.py               # BaseTranslator — 翻译器基类
│   ├── aiping_translator.py        # AipingTranslator — aiping 翻译器实现
│   ├── silicon_flow_translator.py  # SiliconFlowTranslator — 硅基流动翻译器实现
│   ├── qianfan_translator.py       # QianfanTranslator — 百度千帆翻译器实现
│   ├── semantic_analyzer.py        # BaseSemanticAnalyzer — 语义分析器基类
│   ├── aiping_semantic_analyzer.py # AipingSemanticAnalyzer — aiping 语义分析器实现
│   ├── semantic_analyzer_factory.py# SemanticAnalyzerFactory — 语义分析器工厂
│   ├── chapter_identifier.py       # ChapterIdentifier — 章节识别器
│   ├── glossary_extractor.py       # GlossaryExtractor / create_glossary_extractor() — 术语提取器
│   ├── pdf_text_renderer.py        # PdfTextRenderer — PDF 文本渲染（从 PdfGenerator 拆分）
│   ├── pdf_table_renderer.py       # PdfTableRenderer — PDF 表格渲染（从 PdfGenerator 拆分）
│   ├── llm_error_handler.py        # classify_llm_error() — LLM 错误统一分类（生成中文用户友好消息）
│   │
│   ├── extractors/                 # PDF 提取子模块
│   │   ├── __init__.py
│   │   ├── coordinate_utils.py     # 坐标计算工具
│   │   ├── page_utils.py           # 页面处理工具
│   │   ├── style_analyzer.py       # 样式分析器（字体、大小、粗体等）
│   │   ├── table_processor.py      # 表格处理器
│   │   └── text_analyzer.py        # 文本分析器（正文/标题/页眉页脚判断）
│   │
│   └── ocr/                        # OCR 子模块
│       ├── __init__.py
│       ├── base.py                 # BaseOCRExtractor — OCR 提取器基类
│       ├── factory.py              # OCR 工厂，根据引擎类型创建实例
│       ├── paddle_extractor.py     # PaddleOCRExtractor — PaddleOCR 引擎实现
│       ├── llm_extractor.py        # LLMOCRExtractor — LLM OCR 引擎实现（DeepSeek-OCR）
│       ├── llm_response_parser.py  # LlmOcrResponseParser — LLM OCR 响应解析器（从 LlmOcrExtractor 拆分）
│       ├── llm_table_parser.py     # LlmTableParser — LLM OCR 表格解析器（从 LlmOcrExtractor 拆分）
│       ├── ocr_worker.py           # OCR 子进程管理器（心跳、超时、重试）
│       └── system_profiler.py      # 系统资源探针（动态调整 OCR 参数）
│
├── services/                       # 服务编排层
│   ├── translation_service.py      # TranslationService — 翻译流程编排（核心业务逻辑）
│   ├── translation_content.py      # TranslationContentTranslator — 文本翻译子模块（从 TranslationService 拆分）
│   ├── translation_extractor.py    # TranslationExtractor — 翻译器创建与提取子模块（从 TranslationService 拆分）
│   ├── translation_output.py       # TranslationOutputGenerator — 输出生成子模块（从 TranslationService 拆分）
│   ├── translation_table.py        # TranslationTableHandler — 表格翻译子模块（从 TranslationService 拆分）
│   ├── task_service.py             # TaskService — 任务管理（创建、查询、取消）
│   └── glossary_service.py         # GlossaryService — 术语提取流程编排
│
├── cli/                            # CLI 命令处理
│   ├── __init__.py
│   ├── translate_command.py        # translate 子命令处理
│   ├── glossary_command.py         # glossary 子命令处理
│   ├── list_languages_command.py   # list-languages 子命令处理
│   └── progress_display.py         # CLI 进度条显示
│
├── prompts/                        # 提示词规则系统
│   ├── __init__.py                 # 模块初始化
│   ├── rule_registry.py            # PromptRuleRegistry — 语言专项规则注册表（单例）
│   └── language_rules/             # 语言专项规则目录
│       ├── __init__.py             # 规则自动发现与注册
│       ├── base.py                 # 通用基础规则
│       └── bo_to_zh.py             # 藏文→中文专项规则
│
├── utils/                          # 工具函数
│   ├── file_utils.py               # 文件操作（上传校验、目录创建、ZIP 打包、文件删除）
│   ├── logging_config.py           # 日志配置
│   └── text_processing.py          # 文本处理（语义合并、翻译结果拆分）
│
├── templates/                      # Flask HTML 模板
│   ├── index.html                  # 主页（翻译表单）
│   └── download.html               # 下载页
│
├── static/                         # 静态资源
│   ├── css/
│   │   └── style.css               # 样式表
│   └── js/
│       ├── main.js                 # 主页交互逻辑
│       ├── simple_main.js          # 简化版交互
│       └── test_buttons.js         # 测试按钮
│
├── tests/                          # 测试文件
│   ├── conftest.py                 # pytest 配置和共享 fixture
│   ├── data/                       # 测试数据（图片等）
│   ├── test_pdf_extractor.py       # PDF 提取测试
│   ├── test_translation_service.py # 翻译服务测试
│   ├── test_semantic_merge.py      # 语义合并测试
│   ├── test_ocr_extractor.py       # OCR 提取测试
│   ├── ...                         # 其他 60+ 测试文件
│
├── docs/                           # 文档
│   ├── ARCHITECTURE.md             # 项目架构文档
│   ├── TECHNICAL_GUIDE.md          # 技术方案文档
│   ├── DEVELOPMENT_GUIDE.md        # 开发指南文档
│   ├── CHANGELOG.md                # 英文更新日志
│   ├── CHANGELOG.zh.md             # 中文更新日志
│   ├── OCR-requiremnt.md           # OCR 需求文档
│   ├── requirement.md              # 项目需求文档
│   ├── TODO.md                     # 英文待办事项
│   ├── TODO.zh.md                  # 中文待办事项
│   └── ai技术术语表.txt              # AI 技术术语对照表
│
├── plans/                          # 修复计划文档
│   ├── ocr-batch-failure-silent-swallow-fix.md
│   └── ocr-timeout-optimization.md
│
├── prompt/                         # 提示词模板（供 AI 开发使用）
│   ├── merge_branch.md
│   ├── regression_testing.md
│   ├── submit.md
│   ├── update_doc.md
│   └── update_test_case.md
│
├── environment.yml                 # Conda 环境配置
├── install_paddle.sh               # PaddleOCR 安装脚本
├── README.md                       # 英文说明
├── README.zh.md                    # 中文说明
└── LICENSE                         # 许可证
```

---

## 3. 系统架构

系统采用三层架构设计：

```
┌─────────────────────────────────────────────────────────────────┐
│                        入口层 (Entry Layer)                      │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Flask Web   │  │    CLI       │  │   AI IDE Skill       │   │
│  │  (app.py)    │  │  (cli.py)    │  │   (SKILL.md)         │   │
│  │              │  │              │  │                      │   │
│  │ POST /trans  │  │ pdftrans     │  │ Claude Code / Trae   │   │
│  │ POST /gloss  │  │ translate    │  │ 调用 CLI 命令        │   │
│  │ GET  /prog   │  │ glossary     │  │                      │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                      │               │
└─────────┼─────────────────┼──────────────────────┼───────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     服务编排层 (Service Layer)                     │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │ TranslationService   │  │  GlossaryService     │             │
│  │                      │  │                      │             │
│  │ • process_translation│  │ • extract_glossary   │             │
│  │ • translate_content  │  │ • extract_glossary_  │             │
│  │ • translate_tables   │  │   sync               │             │
│  │ • generate_output    │  │                      │             │
│  └──────────┬───────────┘  └──────────┬───────────┘             │
│             │                         │                          │
│  ┌──────────┴───────────┐             │                          │
│  │    TaskService       │             │                          │
│  │ • create_task        │             │                          │
│  │ • get_task           │             │                          │
│  │ • cancel_task        │             │                          │
│  └──────────────────────┘             │                          │
│                                       │                          │
└───────────────────────────────────────┼──────────────────────────┘
                                        │
          ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    核心模块层 (Core Module Layer)                  │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  PdfExtractor   │  │  OCR Engines    │  │  Translators    │  │
│  │  (PyMuPDF)      │  │                 │  │                 │  │
│  │  • extract()    │  │  • PaddleOCR    │  │  • Aiping       │  │
│  │  • get_chapters │  │  • LLM OCR     │  │  • SiliconFlow  │  │
│  │                 │  │                 │  │  • Qianfan      │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                     │           │
│  ┌────────┴────────┐  ┌───────┴─────────┐  ┌───────┴─────────┐ │
│  │ SemanticAnalyzer│  │ ChapterIdenti-  │  │ GlossaryExtrac- │ │
│  │ • aiping        │  │ fier            │  │ tor             │ │
│  │ • silicon_flow  │  │ • identify()    │  │ • extract()     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  PdfGenerator   │  │  DocxGenerator  │  │  MarkdownGen    │  │
│  │  • generate_pdf │  │  • generate_docx│  │  • generate_md  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 层间调用关系

```
入口层 → 服务编排层 → 核心模块层

- Flask Web / CLI / Skill → TranslationService → PdfExtractor / Translators / Generators
- Flask Web / CLI / Skill → GlossaryService   → PdfExtractor / GlossaryExtractor
- TranslationService / GlossaryService → TaskService（任务生命周期管理）
```

---

## 4. 核心数据流

### 4.1 翻译流程七阶段

翻译流程由 `PHASE_CONFIG` 定义，共 7 个阶段，每个阶段映射到 0-100% 的整体进度区间：

| 阶段 | ID | 进度区间 | 说明 |
|------|----|----------|------|
| 1. 初始化 | `init` | 0% - 5% | 保存文件、创建任务 |
| 2. 文本图表提取 | `extraction` | 5% - 40% | PyMuPDF/OCR 提取文本块、表格、图像 |
| 3. 语义合并 | `semantic_merge` | 40% - 50% | 规则合并或 LLM 语义判断合并碎片块 |
| 4. 文本翻译 | `translation` | 50% - 85% | 并行调用翻译 API 翻译合并后的文本块 |
| 5. 表格翻译 | `table_translation` | 85% - 92% | 按行批量翻译表格单元格 |
| 6. 生成输出 | `generation` | 92% - 98% | 生成 PDF / DOCX / Markdown 文件 |
| 7. 清理临时文件 | `clean` | 98% - 100% | 删除上传文件和临时图片 |

### 4.2 术语提取流程三阶段

术语提取流程由 `GLOSSARY_PHASE_CONFIG` 定义：

| 阶段 | ID | 进度区间 | 说明 |
|------|----|----------|------|
| 1. 开始提取 | `init` | 0% - 5% | 保存文件、创建任务 |
| 2. 文本提取 | `pdf_extraction` | 5% - 30% | 提取 PDF 全部页面文本 |
| 3. 术语提取 | `term_extraction` | 30% - 100% | 并行调用 LLM 提取术语 |

### 4.3 数据变换管线

```
PDF 文件
  │
  ▼
PdfExtractor.extract()
  │
  ├── PdfExtraction
  │     ├── pages: [PdfPage]
  │     │     └── text_blocks: [TextBlock]    ← 原始文本块（含样式、位置）
  │     ├── tables: [PdfTable]
  │     │     └── cells: [[PdfCell]]          ← 表格单元格
  │     └── images: [PdfImage]                ← 提取的图像
  │
  ▼  语义合并（可选）
merge_semantic_blocks() / merge_semantic_blocks_with_llm()
  │
  ├── [MergedBlock]                           ← 合并后的语义块
  │     ├── block_text                        ← 合并文本
  │     ├── original_blocks: [TextBlock]      ← 原始块引用
  │     └── max_width / max_height            ← 合并尺寸
  │
  ▼  并行翻译
Translator.translate()
  │
  ├── TranslationResult                       ← 翻译结果
  │     ├── content                           ← 译文文本
  │     ├── token_usage                       ← Token 用量
  │     └── finish_reason                     ← 结束原因
  │
  ▼  拆分翻译结果
split_translated_result()
  │
  ├── [TextBlock]（翻译后）                    ← 保留原始样式和位置
  │
  ▼  生成输出
PdfGenerator / DocxGenerator / MarkdownGenerator
  │
  ├── PDF 文件（保留原始排版覆盖译文）
  ├── DOCX 文件（Word 文档格式）
  └── Markdown 文件（含图像，可选章节拆分为 ZIP）
```

---

## 5. 关键数据模型及关系

### 5.1 模型关系图

```
PdfExtraction
 ├── total_pages: int
 ├── pages: [PdfPage]
 │    └── text_blocks: [TextBlock]  ◄──── MergedBlock.original_blocks
 │                                          │
 ├── tables: [PdfTable]                     ├── block_text
 │    └── cells: [[PdfCell]]                ├── max_width / max_height
 │                                          └── is_formula
 └── images: [PdfImage]

Task
 ├── task_id: str
 ├── status: str (pending/processing/completed/error)
 ├── progress: int (0-100)
 ├── phase_config: dict
 └── current_phase: str

TranslationResult (extends OpenAIResult extends Result)
 ├── content: str
 ├── token_usage: dict
 ├── finish_reason: str
 └── truncation_info: TruncationInfo
      ├── truncated: bool
      ├── token_usage: dict
      └── finish_reason: str
```

### 5.2 模型详细字段

#### TextBlock — 文本块

| 字段 | 类型 | 说明 |
|------|------|------|
| `block_no` | int | 块序号 |
| `block_text` | str | 文本内容 |
| `block_bbox` | tuple | 边界框 (x0, y0, x1, y1) |
| `block_type` | int | 块类型 |
| `page_num` | int | 页码 |
| `font` | str | 字体名称 |
| `font_size` | float | 字体大小 |
| `color` | int | 颜色值 |
| `flags` | int | 样式标记位 |
| `bold` | bool | 是否粗体 |
| `italic` | bool | 是否斜体 |
| `underline` | bool | 是否下划线 |
| `strikethrough` | bool | 是否删除线 |
| `is_body_text` | bool | 是否正文文本 |
| `is_formula` | bool | 是否公式 |
| `alignment` | int | 对齐方式（0=左, 1=居中, 2=右） |
| `chapter_id` | str \| None | 章节ID |
| `chapter_title` | str \| None | 章节标题 |
| `chapter_level` | int | 章节层级 |
| `chapter_number` | str \| None | 章节编号 |

#### PdfPage — 页面

| 字段 | 类型 | 说明 |
|------|------|------|
| `page_num` | int | 页码 |
| `text_blocks` | list[TextBlock] | 文本块列表 |

#### PdfCell — 表格单元格

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | str | 单元格文本 |
| `bbox` | tuple | 边界框 (x0, y0, x1, y1) |
| `row_idx` | int | 行索引 |
| `col_idx` | int | 列索引 |
| `row_span` | int | 跨行数（默认 1） |
| `col_span` | int | 跨列数（默认 1） |
| `alignment` | int | 对齐方式 |
| `estimated_lines` | int | 估算文本行数 |
| `width` | float | 单元格宽度（由 bbox 计算） |
| `height` | float | 单元格高度（由 bbox 计算） |

#### PdfTable — 表格

| 字段 | 类型 | 说明 |
|------|------|------|
| `page_num` | int | 页码 |
| `table_idx` | int | 表格索引 |
| `cells` | list[list[PdfCell]] | 单元格二维列表 |
| `bbox` | tuple \| None | 表格边界框 |
| `row_heights` | list[float] | 行高列表 |
| `col_widths` | list[float] | 列宽列表 |
| `alignment` | int | 表格对齐方式（默认 1=居中） |
| `chapter_id` | str \| None | 章节ID |
| `chapter_title` | str \| None | 章节标题 |
| `chapter_level` | int | 章节层级 |
| `chapter_number` | str \| None | 章节编号 |

#### PdfImage — 图像

| 字段 | 类型 | 说明 |
|------|------|------|
| `page_num` | int | 页码 |
| `image_idx` | int | 图像索引 |
| `image_path` | str | 图像保存路径 |
| `bbox` | tuple | 图像位置 (x0, y0, x1, y1) |
| `chapter_id` | str \| None | 章节ID |
| `chapter_title` | str \| None | 章节标题 |
| `chapter_level` | int | 章节层级 |
| `chapter_number` | str \| None | 章节编号 |

#### PdfExtraction — 整体提取结果

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_pages` | int | PDF 总页数 |
| `pages` | list[PdfPage] | 每页提取结果 |
| `tables` | list[PdfTable] | 表格列表 |
| `images` | list[PdfImage] | 图像列表 |

#### MergedBlock — 合并块

| 字段 | 类型 | 说明 |
|------|------|------|
| `block_text` | str | 合并后的文本 |
| `original_blocks` | list[TextBlock] | 原始 TextBlock 列表 |
| `max_width` | float | 原始块最大宽度 |
| `max_height` | float | 原始块最大高度 |
| `is_formula` | bool | 是否包含公式（自动检测） |
| `font` | str | 字体（取自第一个原始块） |
| `font_size` | float | 字体大小（取自第一个原始块） |
| `bold` | bool | 是否粗体 |
| `italic` | bool | 是否斜体 |
| `color` | int | 字体颜色 |
| `flags` | int | 字体标志位 |
| `page_num` | int | 页码 |

#### Task — 任务

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | str | 任务唯一ID |
| `filename` | str | 原始文件名 |
| `status` | str | 状态：pending / processing / completed / error |
| `progress` | int | 整体进度 0-100 |
| `message` | str | 当前状态消息 |
| `result_file` | str \| None | 结果文件名 |
| `attachments` | list[str] | 附件文件名列表 |
| `error` | str \| None | 错误信息 |
| `canceled` | bool | 是否已取消 |
| `warnings` | list[dict] | 警告列表 |
| `glossary` | str | 术语表内容 |
| `task_type` | str | 任务类型：translation / glossary |
| `phase_config` | dict | 阶段进度配置 |
| `current_phase` | str | 当前阶段 |
| `start_time` | float | 开始时间戳 |
| `end_time` | float \| None | 结束时间戳 |
| `lock` | RLock | 线程安全锁 |

#### TranslationResult — 翻译结果

| 字段 | 类型 | 说明 |
|------|------|------|
| `content` | str | 翻译后的文本 |
| `token_usage` | dict | Token 使用量 |
| `finish_reason` | str | 结束原因（"stop" / "length"） |
| `truncated` | bool | 是否被截断（finish_reason == "length"） |
| `truncation_info` | TruncationInfo | 截断详情 |

---

## 6. 配置系统

配置通过 `config.py` 中的 `Config` 类管理，使用 `python-dotenv` 从 `.env` 文件加载环境变量。

### 6.1 加载机制

```python
from dotenv import load_dotenv
load_dotenv()

class Config:
    # 静态常量保留在类级别
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    SUPPORTED_LANGUAGES = { ... }
    AIPING_EXTRA_BODY = { ... }
    QIANFAN_EXTRA_BODY = { ... }

    def __init__(self):
        """初始化配置，调用 _load() 读取环境变量"""
        self._load()

    def _load(self):
        """（重）加载环境变量配置

        将所有依赖环境变量的属性从类级别移到实例级别（惰性求值）。
        支持在运行时修改环境变量后调用此方法刷新配置。
        """
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        # ... 其他配置项
```

- 启动时自动加载项目根目录下的 `.env` 文件
- `__init__()` 调用 `_load()` 方法，将所有依赖环境变量的属性设为实例级属性
- 不依赖环境变量的静态常量（如 `MAX_CONTENT_LENGTH`、`SUPPORTED_LANGUAGES`、`EXTRA_BODY` 字典）保留在类级别
- `SECRET_KEY` 为必填项，缺失时抛出 `RuntimeError`
- 支持运行时重载：修改环境变量后调用 `_load()` 即可刷新配置

### 6.2 完整配置项列表

#### 基本配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `SECRET_KEY` | `SECRET_KEY` | str | **必填** | Flask 密钥 |
| `DEBUG` | `DEBUG` | bool | `False` | 调试模式 |

#### 上传配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| — | `MAX_CONTENT_LENGTH` | int | 500MB | 最大上传文件大小 |
| — | `UPLOAD_FOLDER` | str | `./uploads` | 上传目录 |
| — | `OUTPUT_FOLDER` | str | `./outputs` | 输出目录 |

#### aiping API 配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `AIPING_API_KEY` | `AIPING_API_KEY` | str | None | aiping API 密钥 |
| `AIPING_API_URL` | `AIPING_API_URL` | str | `https://aiping.cn/api/v1` | aiping API 地址 |
| `AIPING_MODEL_TRANSLATION` | `AIPING_MODEL` | str | `Qwen3-32B` | 翻译模型 |
| `AIPING_MODEL_LAYOUT` | `AIPING_MODEL_LAYOUT` | str | `Qwen3-32B` | Markdown 排版模型 |
| `AIPING_MODEL_GLOSSARY` | `AIPING_MODEL_GLOSSARY` | str | `Qwen3-32B` | 术语提取模型 |

#### 硅基流动 API 配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `SILICON_FLOW_API_KEY` | `SILICON_FLOW_API_KEY` | str | None | 硅基流动 API 密钥 |
| `SILICON_FLOW_API_URL` | `SILICON_FLOW_API_URL` | str | `https://api.siliconflow.cn/v1` | 硅基流动 API 地址 |
| `SILICON_FLOW_MODEL_TRANSLATION` | `SILICON_FLOW_MODEL` | str | `tencent/Hunyuan-MT-7B` | 翻译模型 |
| `SILICON_FLOW_MODEL_LAYOUT` | `SILICON_FLOW_MODEL_LAYOUT` | str | `Qwen/Qwen3-32B` | Markdown 排版模型 |
| `SILICON_FLOW_MODEL_GLOSSARY` | `SILICON_FLOW_MODEL_GLOSSARY` | str | `Qwen/Qwen3-32B` | 术语提取模型 |

#### 百度千帆 API 配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `QIANFAN_API_KEY` | `QIANFAN_API_KEY` | str | None | 百度千帆 API 密钥 |
| `QIANFAN_API_URL` | `QIANFAN_API_URL` | str | `https://qianfan.baidubce.com/v2` | 百度千帆 API 地址 |
| `QIANFAN_MODEL_TRANSLATION` | `QIANFAN_MODEL` | str | `Qwen3-32B` | 翻译模型 |
| `QIANFAN_MODEL_LAYOUT` | `QIANFAN_MODEL_LAYOUT` | str | `Qwen3-32B` | Markdown 排版模型 |
| `QIANFAN_MODEL_GLOSSARY` | `QIANFAN_MODEL_GLOSSARY` | str | `Qwen3-32B` | 术语提取模型 |

#### 语言与文档类型

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| — | `SUPPORTED_LANGUAGES` | dict | 9 种语言 | 支持的语言映射 |
| — | `DEFAULT_SOURCE_LANGUAGE` | str | `en` | 默认源语言 |
| — | `DEFAULT_TARGET_LANGUAGE` | str | `zh` | 默认目标语言 |
| — | `DEFAULT_TRANSLATOR` | str | `aiping` | 默认翻译服务 |
| `DEFAULT_DOC_TYPE` | `DEFAULT_DOC_TYPE` | str | `AI技术` | 默认文档类型 |

#### 线程池配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `MAX_WORKERS` | `MAX_WORKERS` | int | 8 | 最大线程数 |
| `TRANSLATION_BATCH_SIZE` | `TRANSLATION_BATCH_SIZE` | int | 10 | 翻译批处理大小 |

#### 两阶段并行合并配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `USE_TWO_PHASE_MERGE` | `USE_TWO_PHASE_MERGE` | bool | `true` | 是否使用两阶段并行合并 |
| `MERGE_MAX_WORKERS` | `MERGE_MAX_WORKERS` | int | 5 | 并行合并最大线程数 |
| `MERGE_BATCH_SIZE` | `MERGE_BATCH_SIZE` | int | 20 | 每批处理文本对数量 |

#### OCR 配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `USE_OCR` | `USE_OCR` | bool | `false` | 是否启用 OCR 提取 |
| `OCR_ENGINE` | `OCR_ENGINE` | str | `paddleocr` | OCR 引擎类型 |
| `OCR_LANGUAGE` | `OCR_LANGUAGE` | str | `ch` | OCR 识别语言 |
| `OCR_USE_GPU` | `OCR_USE_GPU` | bool | macOS=false, 其他=true | 是否使用 GPU |

#### OCR 内存优化配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `OCR_SKIP_TABLE` | `OCR_SKIP_TABLE` | bool | `false` | 跳过表格识别节省内存 |
| `OCR_SKIP_FORMULA` | `OCR_SKIP_FORMULA` | bool | `false` | 跳过公式识别节省内存 |
| `OCR_PADDLE_DPI` | `OCR_PADDLE_DPI` | int | 120 | PaddleOCR 渲染 DPI（120=内存优化, 150=质量优先） |

#### OCR 超时与重试配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `OCR_HEARTBEAT_TIMEOUT` | `OCR_HEARTBEAT_TIMEOUT` | int | 0 | 心跳超时秒数（0=禁用） |
| `OCR_MAX_TOTAL_TIME` | `OCR_MAX_TOTAL_TIME` | int | 252000 | OCR 最大总执行时间（秒） |
| `OCR_STALL_TIMEOUT` | `OCR_STALL_TIMEOUT` | int | 1800 | OCR 进度停滞超时（秒） |
| `OCR_MAX_RETRIES` | `OCR_MAX_RETRIES` | int | 2 | 子进程崩溃后最大重试次数 |
| `OCR_RETRY_BACKOFF` | `OCR_RETRY_BACKOFF` | float | 5.0 | 重试间隔（秒），每次递增 1.5 倍 |
| `OCR_DYNAMIC_PARAMS` | `OCR_DYNAMIC_PARAMS` | bool | `true` | 根据系统负载动态调整 OCR 参数 |

#### LLM OCR 配置

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `AIPING_OCR_LLM_MODEL` | `AIPING_OCR_LLM_MODEL` | str | `DeepSeek-OCR` | aiping LLM OCR 模型 |
| `SILICON_FLOW_OCR_LLM_MODEL` | `SILICON_FLOW_OCR_LLM_MODEL` | str | `deepseek-ai/DeepSeek-OCR` | 硅基流动 LLM OCR 模型 |
| `QIANFAN_OCR_LLM_MODEL` | `QIANFAN_OCR_LLM_MODEL` | str | `DeepSeek-OCR` | 百度千帆 LLM OCR 模型 |
| `OCR_LLM_MAX_TOKENS` | `OCR_LLM_MAX_TOKENS` | int | 8192 | LLM OCR 最大 Token 数 |
| `OCR_LLM_TEMPERATURE` | `OCR_LLM_TEMPERATURE` | float | 0.1 | LLM OCR 温度 |
| `OCR_LLM_DPI` | `OCR_LLM_DPI` | int | 150 | LLM OCR 渲染 DPI |

#### 按模块 API 参数

| 环境变量 | 配置属性 | 类型 | 默认值 | 说明 |
|----------|----------|------|--------|------|
| `TRANSLATION_TEMPERATURE` | `TRANSLATION_TEMPERATURE` | float | 0.1 | 翻译温度 |
| `TRANSLATION_TOP_P` | `TRANSLATION_TOP_P` | float | 0.9 | 翻译 top_p |
| `TRANSLATION_MAX_TOKENS` | `TRANSLATION_MAX_TOKENS` | int | 8192 | 翻译最大 token 数 |
| `TRANSLATION_TIMEOUT` | `TRANSLATION_TIMEOUT` | int | 30 | 翻译超时（秒） |
| `SEMANTIC_ANALYSIS_TEMPERATURE` | `SEMANTIC_ANALYSIS_TEMPERATURE` | float | 0.1 | 语义分析温度 |
| `SEMANTIC_ANALYSIS_TOP_P` | `SEMANTIC_ANALYSIS_TOP_P` | float | 0.9 | 语义分析 top_p |
| `SEMANTIC_ANALYSIS_SINGLE_MAX_TOKENS` | `SEMANTIC_ANALYSIS_SINGLE_MAX_TOKENS` | int | 1024 | 语义分析单条最大 token |
| `SEMANTIC_ANALYSIS_BATCH_MAX_TOKENS` | `SEMANTIC_ANALYSIS_BATCH_MAX_TOKENS` | int | 2048 | 语义分析批量最大 token |
| `SEMANTIC_ANALYSIS_TIMEOUT` | `SEMANTIC_ANALYSIS_TIMEOUT` | int | 30 | 语义分析超时（秒） |
| `GLOSSARY_TEMPERATURE` | `GLOSSARY_TEMPERATURE` | float | 0.3 | 术语提取温度 |
| `GLOSSARY_MAX_TOKENS` | `GLOSSARY_MAX_TOKENS` | int | 4096 | 术语提取最大 token 数 |
| `GLOSSARY_TIMEOUT` | `GLOSSARY_TIMEOUT` | int | 30 | 术语提取超时（秒） |
| `LAYOUT_TEMPERATURE` | `LAYOUT_TEMPERATURE` | float | 0.1 | Markdown 排版温度 |
| `LAYOUT_MAX_TOKENS` | `LAYOUT_MAX_TOKENS` | int | 8192 | Markdown 排版最大 token 数 |

---

## 7. 外部服务依赖

### 7.1 aiping

| 项目 | 说明 |
|------|------|
| **用途** | 翻译、语义分析、术语提取、LLM OCR、Markdown 排版 |
| **API 格式** | OpenAI 兼容 API（`/v1/chat/completions`） |
| **API 地址** | `https://aiping.cn/api/v1` |
| **认证方式** | Bearer Token（`AIPING_API_KEY`） |

**默认模型：**

| 功能 | 配置项 | 默认模型 |
|------|--------|----------|
| 翻译 | `AIPING_MODEL` | `Qwen3-32B` |
| Markdown 排版 | `AIPING_MODEL_LAYOUT` | `Qwen3-32B` |
| 术语提取 | `AIPING_MODEL_GLOSSARY` | `Qwen3-32B` |
| LLM OCR | `AIPING_OCR_LLM_MODEL` | `DeepSeek-OCR` |

**额外请求参数（`AIPING_EXTRA_BODY`）：**

```python
{
    "enable_thinking": False,
    "provider": {
        "only": [],
        "order": [],
        "sort": "output_price",
        "input_price_range": [],
        "output_price_range": [],
        "input_length_range": [],
        "throughput_range": [],
        "latency_range": []
    }
}
```

### 7.2 硅基流动 SiliconFlow

| 项目 | 说明 |
|------|------|
| **用途** | 翻译、语义分析、术语提取、LLM OCR、Markdown 排版 |
| **API 格式** | OpenAI 兼容 API（`/v1/chat/completions`） |
| **API 地址** | `https://api.siliconflow.cn/v1` |
| **认证方式** | Bearer Token（`SILICON_FLOW_API_KEY`） |

**默认模型：**

| 功能 | 配置项 | 默认模型 |
|------|--------|----------|
| 翻译 | `SILICON_FLOW_MODEL` | `tencent/Hunyuan-MT-7B` |
| Markdown 排版 | `SILICON_FLOW_MODEL_LAYOUT` | `Qwen/Qwen3-32B` |
| 术语提取 | `SILICON_FLOW_MODEL_GLOSSARY` | `Qwen/Qwen3-32B` |
| LLM OCR | `SILICON_FLOW_OCR_LLM_MODEL` | `deepseek-ai/DeepSeek-OCR` |

**额外请求参数（`SILICON_FLOW_EXTRA_BODY`）：**

```python
{
    "enable_thinking": False
}
```

### 7.3 百度千帆 Qianfan

| 项目 | 说明 |
|------|------|
| **用途** | 翻译、语义分析、术语提取、LLM OCR、Markdown 排版 |
| **API 格式** | OpenAI 兼容 API（`/v2/chat/completions`） |
| **API 地址** | `https://qianfan.baidubce.com/v2` |
| **认证方式** | Bearer Token（`QIANFAN_API_KEY`） |

**默认模型：**

| 功能 | 配置项 | 默认模型 |
|------|--------|----------|
| 翻译 | `QIANFAN_MODEL` | `Qwen3-32B` |
| Markdown 排版 | `QIANFAN_MODEL_LAYOUT` | `Qwen3-32B` |
| 术语提取 | `QIANFAN_MODEL_GLOSSARY` | `Qwen3-32B` |
| LLM OCR | `QIANFAN_OCR_LLM_MODEL` | `DeepSeek-OCR` |

**额外请求参数（`QIANFAN_EXTRA_BODY`）：**

```python
{
    "enable_thinking": False,            # Qwen3 系列关闭思考
    "thinking": {"type": "disabled"},    # GLM-4.5+/5.x 系列关闭思考
}
```

> **说明**：千帆平台同时使用 GLM-5.1（翻译）和 Qwen3-32B（排版/术语），两类模型使用不同的思考关闭参数。`enable_thinking` 是 Qwen3 特有参数，`thinking.type` 是 GLM-4.5+ 特有参数，各模型服务端会忽略自身不识别的参数，互不冲突。

### 7.4 PaddleOCR

| 项目 | 说明 |
|------|------|
| **用途** | 本地 OCR 引擎，用于扫描版 PDF 的文字、表格、公式识别 |
| **版本** | PP-StructureV3 |
| **运行方式** | 子进程（`ocr_worker.py` 管理），支持心跳检测、超时、重试 |
| **依赖** | `paddlepaddle` / `paddlepaddle-gpu` + `paddleocr` |
| **GPU 支持** | macOS 默认 CPU，其他平台默认 GPU（可通过 `OCR_USE_GPU` 配置） |

**关键特性：**

- 版面分析：识别文本区域、表格区域、图像区域
- 公式识别：识别数学公式并转换为 LaTeX 格式
- 表格识别：识别表格结构并提取单元格
- 动态参数调整：根据系统内存和 CPU 自动调整 OCR 参数（`OCR_DYNAMIC_PARAMS`）
- 三层保护机制：心跳超时、总时间限制、进度停滞检测
