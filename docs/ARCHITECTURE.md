# pdfTrans Project Architecture Document

## 1. Project Positioning & Core Features

pdfTrans is a PDF translation tool that supports three invocation methods: **Web UI**, **Command Line (CLI)**, and **AI IDE Skill**.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| PDF Text Extraction | Extract text blocks, tables, images, and style information based on PyMuPDF |
| OCR Text Recognition | Supports PaddleOCR (PP-StructureV3 local engine) and LLM OCR (DeepSeek-OCR cloud engine) |
| Multi-Translation API | Supports aiping (OpenAI-compatible API), SiliconFlow (OpenAI-compatible API), and Baidu Qianfan (OpenAI-compatible API) |
| Multi-Format Output | PDF (preserving original layout), DOCX (Word document), Markdown (with chapter splitting) |
| Glossary Extraction | Automatically extract specialized terminology and translation mappings from PDFs |
| Semantic Merging | Rule-based merging or LLM semantic judgment merging to reduce translation fragmentation |
| Chapter Identification | Automatically identify document chapter structure; supports output split by chapters |

### Supported Languages (9-way mutual translation)

| Code | Language | Code | Language |
|------|----------|------|----------|
| zh | Chinese | en | English |
| ja | Japanese | ko | Korean |
| fr | French | de | German |
| es | Spanish | ru | Russian |
| bo | Tibetan | | |

---

## 2. Directory Structure

```
pdfTrans/
├── app.py                          # Flask Web entry point, provides HTTP APIs for translation and glossary extraction
├── cli.py                          # CLI entry point, argparse subcommand routing
├── config.py                       # Configuration class, loads all environment variables from .env
├── SKILL.md                        # AI IDE Skill definition file (Claude Code / Trae, etc.)
├── .env.example                    # Environment variable template
│
├── models/                         # Data model layer
│   ├── copyable.py                 # CopyableMixin base class, provides copy() and serialization
│   ├── text_block.py               # TextBlock — PDF text block model
│   ├── extraction.py               # PdfPage / PdfCell / PdfTable / PdfImage / PdfExtraction — extraction result models
│   ├── merged_block.py             # MergedBlock — semantically merged block model
│   ├── task.py                     # Task — async task model (with status, progress, lock)
│   ├── phase_config.py             # PHASE_CONFIG / GLOSSARY_PHASE_CONFIG — phase progress configuration
│   └── result_types.py             # TruncationInfo / Result / OpenAIResult / TranslationResult / MarkdownResult / MarkdownGenerationResult
│
├── modules/                        # Core module layer
│   ├── pdf_extractor.py            # PdfExtractor — PDF text/table/image extraction (PyMuPDF)
│   ├── pdf_generator.py            # PdfGenerator — generate translated PDF
│   ├── docx_generator.py           # DocxGenerator — generate translated Word document
│   ├── markdown_generator.py       # MarkdownGenerator — generate translated Markdown (with LLM layout)
│   ├── translator.py               # BaseTranslator — translator base class
│   ├── aiping_translator.py        # AipingTranslator — aiping translator implementation
│   ├── silicon_flow_translator.py  # SiliconFlowTranslator — SiliconFlow translator implementation
│   ├── qianfan_translator.py       # QianfanTranslator — Baidu Qianfan translator implementation
│   ├── semantic_analyzer.py        # BaseSemanticAnalyzer — semantic analyzer base class
│   ├── aiping_semantic_analyzer.py # AipingSemanticAnalyzer — aiping semantic analyzer implementation
│   ├── semantic_analyzer_factory.py# SemanticAnalyzerFactory — semantic analyzer factory
│   ├── chapter_identifier.py       # ChapterIdentifier — chapter identifier
│   ├── glossary_extractor.py       # GlossaryExtractor / create_glossary_extractor() — glossary extractor
│   ├── pdf_text_renderer.py        # PdfTextRenderer — PDF text rendering (split from PdfGenerator)
│   ├── pdf_table_renderer.py       # PdfTableRenderer — PDF table rendering (split from PdfGenerator)
│   ├── llm_error_handler.py        # classify_llm_error() — unified LLM error classification (Chinese user-friendly messages)
│   │
│   ├── extractors/                 # PDF extraction sub-module
│   │   ├── __init__.py
│   │   ├── coordinate_utils.py     # Coordinate calculation utilities
│   │   ├── page_utils.py           # Page processing utilities
│   │   ├── style_analyzer.py       # Style analyzer (font, size, bold, etc.)
│   │   ├── table_processor.py      # Table processor
│   │   └── text_analyzer.py        # Text analyzer (body text/heading/header/footer classification)
│   │
│   └── ocr/                        # OCR sub-module
│       ├── __init__.py
│       ├── base.py                 # BaseOCRExtractor — OCR extractor base class
│       ├── factory.py              # OCR factory, creates instances based on engine type
│       ├── paddle_extractor.py     # PaddleOCRExtractor — PaddleOCR engine implementation
│       ├── llm_extractor.py        # LLMOCRExtractor — LLM OCR engine implementation (DeepSeek-OCR)
│       ├── llm_response_parser.py  # LlmOcrResponseParser — LLM OCR response parser (split from LlmOcrExtractor)
│       ├── llm_table_parser.py     # LlmTableParser — LLM OCR table parser (split from LlmOcrExtractor)
│       ├── ocr_worker.py           # OCR subprocess manager (heartbeat, timeout, retry)
│       └── system_profiler.py      # System resource profiler (dynamically adjusts OCR parameters)
│
├── services/                       # Service orchestration layer
│   ├── translation_service.py      # TranslationService — translation workflow orchestration (core business logic)
│   ├── translation_content.py      # TranslationContentTranslator — text translation sub-module (split from TranslationService)
│   ├── translation_extractor.py    # TranslationExtractor — translator creation and extraction sub-module (split from TranslationService)
│   ├── translation_output.py       # TranslationOutputGenerator — output generation sub-module (split from TranslationService)
│   ├── translation_table.py        # TranslationTableHandler — table translation sub-module (split from TranslationService)
│   ├── task_service.py             # TaskService — task management (create, query, cancel)
│   └── glossary_service.py         # GlossaryService — glossary extraction workflow orchestration
│
├── cli/                            # CLI command handlers
│   ├── __init__.py
│   ├── translate_command.py        # translate subcommand handler
│   ├── glossary_command.py         # glossary subcommand handler
│   ├── list_languages_command.py   # list-languages subcommand handler
│   └── progress_display.py         # CLI progress bar display
│
├── prompts/                        # Prompt rule system
│   ├── __init__.py                 # Module initialization
│   ├── rule_registry.py            # PromptRuleRegistry — language-specific rule registry (singleton)
│   └── language_rules/             # Language-specific rules directory
│       ├── __init__.py             # Auto-discovery and registration of rules
│       ├── base.py                 # Common base rules
│       └── bo_to_zh.py             # Tibetan→Chinese specific rules
│
├── utils/                          # Utility functions
│   ├── file_utils.py               # File operations (upload validation, directory creation, ZIP packaging, file deletion)
│   ├── logging_config.py           # Logging configuration
│   └── text_processing.py          # Text processing (semantic merging, translation result splitting)
│
├── templates/                      # Flask HTML templates
│   ├── index.html                  # Home page (translation form)
│   └── download.html               # Download page
│
├── static/                         # Static assets
│   ├── css/
│   │   └── style.css               # Stylesheet
│   └── js/
│       ├── main.js                 # Home page interaction logic
│       ├── simple_main.js          # Simplified interaction
│       └── test_buttons.js         # Test buttons
│
├── tests/                          # Test files
│   ├── conftest.py                 # pytest configuration and shared fixtures
│   ├── data/                       # Test data (images, etc.)
│   ├── test_pdf_extractor.py       # PDF extraction tests
│   ├── test_translation_service.py # Translation service tests
│   ├── test_semantic_merge.py      # Semantic merge tests
│   ├── test_ocr_extractor.py       # OCR extraction tests
│   ├── ...                         # Other 60+ test files
│
├── docs/                           # Documentation
│   ├── ARCHITECTURE.md             # Project architecture document
│   ├── TECHNICAL_GUIDE.md          # Technical guide document
│   ├── DEVELOPMENT_GUIDE.md        # Development guide document
│   ├── CHANGELOG.md                # English changelog
│   ├── CHANGELOG.zh.md             # Chinese changelog
│   ├── OCR-requiremnt.md           # OCR requirements document
│   ├── requirement.md              # Project requirements document
│   ├── TODO.md                     # English TODO list
│   ├── TODO.zh.md                  # Chinese TODO list
│   └── ai技术术语表.txt              # AI technical terminology reference
│
├── plans/                          # Fix plan documents
│   ├── ocr-batch-failure-silent-swallow-fix.md
│   └── ocr-timeout-optimization.md
│
├── prompt/                         # Prompt templates (for AI-assisted development)
│   ├── merge_branch.md
│   ├── regression_testing.md
│   ├── submit.md
│   ├── update_doc.md
│   └── update_test_case.md
│
├── environment.yml                 # Conda environment configuration
├── install_paddle.sh               # PaddleOCR installation script
├── README.md                       # English README
├── README.zh.md                    # Chinese README
└── LICENSE                         # License
```

---

## 3. System Architecture

The system uses a three-layer architecture design:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Entry Layer                               │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Flask Web   │  │    CLI       │  │   AI IDE Skill       │   │
│  │  (app.py)    │  │  (cli.py)    │  │   (SKILL.md)         │   │
│  │              │  │              │  │                      │   │
│  │ POST /trans  │  │ pdftrans     │  │ Claude Code / Trae   │   │
│  │ POST /gloss  │  │ translate    │  │ invokes CLI commands │   │
│  │ GET  /prog   │  │ glossary     │  │                      │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                      │               │
└─────────┼─────────────────┼──────────────────────┼───────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Service Orchestration Layer                   │
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
│                    Core Module Layer                              │
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

### Inter-Layer Call Relationships

```
Entry Layer → Service Orchestration Layer → Core Module Layer

- Flask Web / CLI / Skill → TranslationService → PdfExtractor / Translators / Generators
- Flask Web / CLI / Skill → GlossaryService   → PdfExtractor / GlossaryExtractor
- TranslationService / GlossaryService → TaskService (task lifecycle management)
```

---

## 4. Core Data Flow

### 4.1 Translation Pipeline — Seven Phases

The translation pipeline is defined by `PHASE_CONFIG` with 7 phases, each mapped to a 0-100% overall progress range:

| Phase | ID | Progress Range | Description |
|-------|----|----------------|-------------|
| 1. Initialization | `init` | 0% - 5% | Save file, create task |
| 2. Text & Table Extraction | `extraction` | 5% - 40% | Extract text blocks, tables, and images via PyMuPDF/OCR |
| 3. Semantic Merging | `semantic_merge` | 40% - 50% | Rule-based merging or LLM semantic judgment merging of fragmented blocks |
| 4. Text Translation | `translation` | 50% - 85% | Parallel translation API calls for merged text blocks |
| 5. Table Translation | `table_translation` | 85% - 92% | Batch-translate table cells row by row |
| 6. Output Generation | `generation` | 92% - 98% | Generate PDF / DOCX / Markdown files |
| 7. Cleanup | `clean` | 98% - 100% | Delete uploaded files and temporary images |

### 4.2 Glossary Extraction Pipeline — Three Phases

The glossary extraction pipeline is defined by `GLOSSARY_PHASE_CONFIG`:

| Phase | ID | Progress Range | Description |
|-------|----|----------------|-------------|
| 1. Start Extraction | `init` | 0% - 5% | Save file, create task |
| 2. Text Extraction | `pdf_extraction` | 5% - 30% | Extract text from all PDF pages |
| 3. Term Extraction | `term_extraction` | 30% - 100% | Parallel LLM calls to extract terminology |

### 4.3 Data Transformation Pipeline

```
PDF File
  │
  ▼
PdfExtractor.extract()
  │
  ├── PdfExtraction
  │     ├── pages: [PdfPage]
  │     │     └── text_blocks: [TextBlock]    ← Raw text blocks (with style and position)
  │     ├── tables: [PdfTable]
  │     │     └── cells: [[PdfCell]]          ← Table cells
  │     └── images: [PdfImage]                ← Extracted images
  │
  ▼  Semantic Merging (optional)
merge_semantic_blocks() / merge_semantic_blocks_with_llm()
  │
  ├── [MergedBlock]                           ← Merged semantic blocks
  │     ├── block_text                        ← Merged text
  │     ├── original_blocks: [TextBlock]      ← References to original blocks
  │     └── max_width / max_height            ← Merged dimensions
  │
  ▼  Parallel Translation
Translator.translate()
  │
  ├── TranslationResult                       ← Translation result
  │     ├── content                           ← Translated text
  │     ├── token_usage                       ← Token usage
  │     └── finish_reason                     ← Finish reason
  │
  ▼  Split Translation Results
split_translated_result()
  │
  ├── [TextBlock] (translated)                ← Preserves original style and position
  │
  ▼  Generate Output
PdfGenerator / DocxGenerator / MarkdownGenerator
  │
  ├── PDF file (overlays translated text preserving original layout)
  ├── DOCX file (Word document format)
  └── Markdown file (with images, optional chapter splitting as ZIP)
```

---

## 5. Key Data Models & Relationships

### 5.1 Model Relationship Diagram

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

### 5.2 Model Field Details

#### TextBlock — Text Block

| Field | Type | Description |
|-------|------|-------------|
| `block_no` | int | Block sequence number |
| `block_text` | str | Text content |
| `block_bbox` | tuple | Bounding box (x0, y0, x1, y1) |
| `block_type` | int | Block type |
| `page_num` | int | Page number |
| `font` | str | Font name |
| `font_size` | float | Font size |
| `color` | int | Color value |
| `flags` | int | Style flag bits |
| `bold` | bool | Whether bold |
| `italic` | bool | Whether italic |
| `underline` | bool | Whether underlined |
| `strikethrough` | bool | Whether strikethrough |
| `is_body_text` | bool | Whether body text |
| `is_formula` | bool | Whether a formula |
| `alignment` | int | Alignment (0=left, 1=center, 2=right) |
| `chapter_id` | str \| None | Chapter ID |
| `chapter_title` | str \| None | Chapter title |
| `chapter_level` | int | Chapter level |
| `chapter_number` | str \| None | Chapter number |

#### PdfPage — Page

| Field | Type | Description |
|-------|------|-------------|
| `page_num` | int | Page number |
| `text_blocks` | list[TextBlock] | List of text blocks |

#### PdfCell — Table Cell

| Field | Type | Description |
|-------|------|-------------|
| `text` | str | Cell text |
| `bbox` | tuple | Bounding box (x0, y0, x1, y1) |
| `row_idx` | int | Row index |
| `col_idx` | int | Column index |
| `row_span` | int | Row span (default 1) |
| `col_span` | int | Column span (default 1) |
| `alignment` | int | Alignment |
| `estimated_lines` | int | Estimated number of text lines |
| `width` | float | Cell width (computed from bbox) |
| `height` | float | Cell height (computed from bbox) |

#### PdfTable — Table

| Field | Type | Description |
|-------|------|-------------|
| `page_num` | int | Page number |
| `table_idx` | int | Table index |
| `cells` | list[list[PdfCell]] | 2D list of cells |
| `bbox` | tuple \| None | Table bounding box |
| `row_heights` | list[float] | List of row heights |
| `col_widths` | list[float] | List of column widths |
| `alignment` | int | Table alignment (default 1=center) |
| `chapter_id` | str \| None | Chapter ID |
| `chapter_title` | str \| None | Chapter title |
| `chapter_level` | int | Chapter level |
| `chapter_number` | str \| None | Chapter number |

#### PdfImage — Image

| Field | Type | Description |
|-------|------|-------------|
| `page_num` | int | Page number |
| `image_idx` | int | Image index |
| `image_path` | str | Image save path |
| `bbox` | tuple | Image position (x0, y0, x1, y1) |
| `chapter_id` | str \| None | Chapter ID |
| `chapter_title` | str \| None | Chapter title |
| `chapter_level` | int | Chapter level |
| `chapter_number` | str \| None | Chapter number |

#### PdfExtraction — Overall Extraction Result

| Field | Type | Description |
|-------|------|-------------|
| `total_pages` | int | Total number of PDF pages |
| `pages` | list[PdfPage] | Per-page extraction results |
| `tables` | list[PdfTable] | List of tables |
| `images` | list[PdfImage] | List of images |

#### MergedBlock — Merged Block

| Field | Type | Description |
|-------|------|-------------|
| `block_text` | str | Merged text |
| `original_blocks` | list[TextBlock] | List of original TextBlocks |
| `max_width` | float | Maximum width of original blocks |
| `max_height` | float | Maximum height of original blocks |
| `is_formula` | bool | Whether it contains a formula (auto-detected) |
| `font` | str | Font (taken from first original block) |
| `font_size` | float | Font size (taken from first original block) |
| `bold` | bool | Whether bold |
| `italic` | bool | Whether italic |
| `color` | int | Font color |
| `flags` | int | Font flag bits |
| `page_num` | int | Page number |

#### Task — Task

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | str | Unique task ID |
| `filename` | str | Original filename |
| `status` | str | Status: pending / processing / completed / error |
| `progress` | int | Overall progress 0-100 |
| `message` | str | Current status message |
| `result_file` | str \| None | Result filename |
| `attachments` | list[str] | List of attachment filenames |
| `error` | str \| None | Error message |
| `canceled` | bool | Whether canceled |
| `warnings` | list[dict] | List of warnings |
| `glossary` | str | Glossary content |
| `task_type` | str | Task type: translation / glossary |
| `phase_config` | dict | Phase progress configuration |
| `current_phase` | str | Current phase |
| `start_time` | float | Start timestamp |
| `end_time` | float \| None | End timestamp |
| `lock` | RLock | Thread-safe lock |

#### TranslationResult — Translation Result

| Field | Type | Description |
|-------|------|-------------|
| `content` | str | Translated text |
| `token_usage` | dict | Token usage |
| `finish_reason` | str | Finish reason ("stop" / "length") |
| `truncated` | bool | Whether truncated (finish_reason == "length") |
| `truncation_info` | TruncationInfo | Truncation details |

---

## 6. Configuration System

Configuration is managed through the `Config` class in `config.py`, which uses `python-dotenv` to load environment variables from a `.env` file.

### 6.1 Loading Mechanism

```python
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Static constants remain at class level
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    SUPPORTED_LANGUAGES = { ... }
    AIPING_EXTRA_BODY = { ... }
    QIANFAN_EXTRA_BODY = { ... }

    def __init__(self):
        """Initialize configuration, calls _load() to read environment variables"""
        self._load()

    def _load(self):
        """(Re)load environment variable configuration

        Moves all environment-dependent attributes from class level to instance level (lazy evaluation).
        Supports refreshing configuration at runtime by calling this method after modifying environment variables.
        """
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        # ... other configuration items
```

- Automatically loads the `.env` file in the project root directory on startup
- `__init__()` calls `_load()` method, setting all environment-dependent attributes as instance-level attributes
- Static constants that don't depend on environment variables (e.g., `MAX_CONTENT_LENGTH`, `SUPPORTED_LANGUAGES`, `EXTRA_BODY` dicts) remain at class level
- `SECRET_KEY` is required; a `RuntimeError` is raised if missing
- Supports runtime reload: call `_load()` to refresh configuration after modifying environment variables

### 6.2 Complete Configuration Reference

#### Basic Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `SECRET_KEY` | `SECRET_KEY` | str | **Required** | Flask secret key |
| `DEBUG` | `DEBUG` | bool | `False` | Debug mode |

#### Upload Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| — | `MAX_CONTENT_LENGTH` | int | 500MB | Maximum upload file size |
| — | `UPLOAD_FOLDER` | str | `./uploads` | Upload directory |
| — | `OUTPUT_FOLDER` | str | `./outputs` | Output directory |

#### aiping API Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `AIPING_API_KEY` | `AIPING_API_KEY` | str | None | aiping API key |
| `AIPING_API_URL` | `AIPING_API_URL` | str | `https://aiping.cn/api/v1` | aiping API URL |
| `AIPING_MODEL_TRANSLATION` | `AIPING_MODEL` | str | `Qwen3-32B` | Translation model |
| `AIPING_MODEL_LAYOUT` | `AIPING_MODEL_LAYOUT` | str | `Qwen3-32B` | Markdown layout model |
| `AIPING_MODEL_GLOSSARY` | `AIPING_MODEL_GLOSSARY` | str | `Qwen3-32B` | Glossary extraction model |

#### SiliconFlow API Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `SILICON_FLOW_API_KEY` | `SILICON_FLOW_API_KEY` | str | None | SiliconFlow API key |
| `SILICON_FLOW_API_URL` | `SILICON_FLOW_API_URL` | str | `https://api.siliconflow.cn/v1` | SiliconFlow API URL |
| `SILICON_FLOW_MODEL_TRANSLATION` | `SILICON_FLOW_MODEL` | str | `tencent/Hunyuan-MT-7B` | Translation model |
| `SILICON_FLOW_MODEL_LAYOUT` | `SILICON_FLOW_MODEL_LAYOUT` | str | `Qwen/Qwen3-32B` | Markdown layout model |
| `SILICON_FLOW_MODEL_GLOSSARY` | `SILICON_FLOW_MODEL_GLOSSARY` | str | `Qwen/Qwen3-32B` | Glossary extraction model |

#### Baidu Qianfan API Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `QIANFAN_API_KEY` | `QIANFAN_API_KEY` | str | None | Baidu Qianfan API key |
| `QIANFAN_API_URL` | `QIANFAN_API_URL` | str | `https://qianfan.baidubce.com/v2` | Baidu Qianfan API URL |
| `QIANFAN_MODEL_TRANSLATION` | `QIANFAN_MODEL` | str | `Qwen3-32B` | Translation model |
| `QIANFAN_MODEL_LAYOUT` | `QIANFAN_MODEL_LAYOUT` | str | `Qwen3-32B` | Markdown layout model |
| `QIANFAN_MODEL_GLOSSARY` | `QIANFAN_MODEL_GLOSSARY` | str | `Qwen3-32B` | Glossary extraction model |

#### Language & Document Type

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| — | `SUPPORTED_LANGUAGES` | dict | 9 languages | Supported language mapping |
| — | `DEFAULT_SOURCE_LANGUAGE` | str | `en` | Default source language |
| — | `DEFAULT_TARGET_LANGUAGE` | str | `zh` | Default target language |
| — | `DEFAULT_TRANSLATOR` | str | `aiping` | Default translation service |
| `DEFAULT_DOC_TYPE` | `DEFAULT_DOC_TYPE` | str | `AI技术` | Default document type |

#### Thread Pool Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `MAX_WORKERS` | `MAX_WORKERS` | int | 8 | Maximum number of threads |
| `TRANSLATION_BATCH_SIZE` | `TRANSLATION_BATCH_SIZE` | int | 10 | Translation batch size |

#### Two-Phase Parallel Merge Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `USE_TWO_PHASE_MERGE` | `USE_TWO_PHASE_MERGE` | bool | `true` | Whether to use two-phase parallel merge |
| `MERGE_MAX_WORKERS` | `MERGE_MAX_WORKERS` | int | 5 | Maximum threads for parallel merge |
| `MERGE_BATCH_SIZE` | `MERGE_BATCH_SIZE` | int | 20 | Number of text pairs per batch |

#### OCR Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `USE_OCR` | `USE_OCR` | bool | `false` | Whether to enable OCR extraction |
| `OCR_ENGINE` | `OCR_ENGINE` | str | `paddleocr` | OCR engine type |
| `OCR_LANGUAGE` | `OCR_LANGUAGE` | str | `ch` | OCR recognition language |
| `OCR_USE_GPU` | `OCR_USE_GPU` | bool | macOS=false, others=true | Whether to use GPU |

#### OCR Memory Optimization Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `OCR_SKIP_TABLE` | `OCR_SKIP_TABLE` | bool | `false` | Skip table recognition to save memory |
| `OCR_SKIP_FORMULA` | `OCR_SKIP_FORMULA` | bool | `false` | Skip formula recognition to save memory |
| `OCR_PADDLE_DPI` | `OCR_PADDLE_DPI` | int | 120 | PaddleOCR render DPI (120=memory-optimized, 150=quality-prioritized) |

#### OCR Timeout & Retry Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `OCR_HEARTBEAT_TIMEOUT` | `OCR_HEARTBEAT_TIMEOUT` | int | 0 | Heartbeat timeout in seconds (0=disabled) |
| `OCR_MAX_TOTAL_TIME` | `OCR_MAX_TOTAL_TIME` | int | 252000 | OCR maximum total execution time (seconds) |
| `OCR_STALL_TIMEOUT` | `OCR_STALL_TIMEOUT` | int | 1800 | OCR progress stall timeout (seconds) |
| `OCR_MAX_RETRIES` | `OCR_MAX_RETRIES` | int | 2 | Maximum retry count after subprocess crash |
| `OCR_RETRY_BACKOFF` | `OCR_RETRY_BACKOFF` | float | 5.0 | Retry interval (seconds), increments by 1.5x each time |
| `OCR_DYNAMIC_PARAMS` | `OCR_DYNAMIC_PARAMS` | bool | `true` | Dynamically adjust OCR parameters based on system load |

#### LLM OCR Configuration

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `AIPING_OCR_LLM_MODEL` | `AIPING_OCR_LLM_MODEL` | str | `DeepSeek-OCR` | aiping LLM OCR model |
| `SILICON_FLOW_OCR_LLM_MODEL` | `SILICON_FLOW_OCR_LLM_MODEL` | str | `deepseek-ai/DeepSeek-OCR` | SiliconFlow LLM OCR model |
| `QIANFAN_OCR_LLM_MODEL` | `QIANFAN_OCR_LLM_MODEL` | str | `DeepSeek-OCR` | Baidu Qianfan LLM OCR model |
| `OCR_LLM_MAX_TOKENS` | `OCR_LLM_MAX_TOKENS` | int | 8192 | LLM OCR maximum token count |
| `OCR_LLM_TEMPERATURE` | `OCR_LLM_TEMPERATURE` | float | 0.1 | LLM OCR temperature |
| `OCR_LLM_DPI` | `OCR_LLM_DPI` | int | 150 | LLM OCR render DPI |

#### Per-Module API Parameters

| Environment Variable | Config Property | Type | Default | Description |
|---------------------|-----------------|------|---------|-------------|
| `TRANSLATION_TEMPERATURE` | `TRANSLATION_TEMPERATURE` | float | 0.1 | Translation temperature |
| `TRANSLATION_TOP_P` | `TRANSLATION_TOP_P` | float | 0.9 | Translation top_p |
| `TRANSLATION_MAX_TOKENS` | `TRANSLATION_MAX_TOKENS` | int | 8192 | Translation max tokens |
| `TRANSLATION_TIMEOUT` | `TRANSLATION_TIMEOUT` | int | 30 | Translation timeout (seconds) |
| `SEMANTIC_ANALYSIS_TEMPERATURE` | `SEMANTIC_ANALYSIS_TEMPERATURE` | float | 0.1 | Semantic analysis temperature |
| `SEMANTIC_ANALYSIS_TOP_P` | `SEMANTIC_ANALYSIS_TOP_P` | float | 0.9 | Semantic analysis top_p |
| `SEMANTIC_ANALYSIS_SINGLE_MAX_TOKENS` | `SEMANTIC_ANALYSIS_SINGLE_MAX_TOKENS` | int | 1024 | Semantic analysis single max tokens |
| `SEMANTIC_ANALYSIS_BATCH_MAX_TOKENS` | `SEMANTIC_ANALYSIS_BATCH_MAX_TOKENS` | int | 2048 | Semantic analysis batch max tokens |
| `SEMANTIC_ANALYSIS_TIMEOUT` | `SEMANTIC_ANALYSIS_TIMEOUT` | int | 30 | Semantic analysis timeout (seconds) |
| `GLOSSARY_TEMPERATURE` | `GLOSSARY_TEMPERATURE` | float | 0.3 | Glossary extraction temperature |
| `GLOSSARY_MAX_TOKENS` | `GLOSSARY_MAX_TOKENS` | int | 4096 | Glossary extraction max tokens |
| `GLOSSARY_TIMEOUT` | `GLOSSARY_TIMEOUT` | int | 30 | Glossary extraction timeout (seconds) |
| `LAYOUT_TEMPERATURE` | `LAYOUT_TEMPERATURE` | float | 0.1 | Markdown layout temperature |
| `LAYOUT_MAX_TOKENS` | `LAYOUT_MAX_TOKENS` | int | 8192 | Markdown layout max tokens |

---

## 7. External Service Dependencies

### 7.1 aiping

| Item | Description |
|------|-------------|
| **Purpose** | Translation, semantic analysis, glossary extraction, LLM OCR, Markdown layout |
| **API Format** | OpenAI-compatible API (`/v1/chat/completions`) |
| **API URL** | `https://aiping.cn/api/v1` |
| **Authentication** | Bearer Token (`AIPING_API_KEY`) |

**Default Models:**

| Function | Config Key | Default Model |
|----------|-----------|---------------|
| Translation | `AIPING_MODEL` | `Qwen3-32B` |
| Markdown Layout | `AIPING_MODEL_LAYOUT` | `Qwen3-32B` |
| Glossary Extraction | `AIPING_MODEL_GLOSSARY` | `Qwen3-32B` |
| LLM OCR | `AIPING_OCR_LLM_MODEL` | `DeepSeek-OCR` |

**Extra Request Parameters (`AIPING_EXTRA_BODY`)**

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

### 7.2 SiliconFlow

| Item | Description |
|------|-------------|
| **Purpose** | Translation, semantic analysis, glossary extraction, LLM OCR, Markdown layout |
| **API Format** | OpenAI-compatible API (`/v1/chat/completions`) |
| **API URL** | `https://api.siliconflow.cn/v1` |
| **Authentication** | Bearer Token (`SILICON_FLOW_API_KEY`) |

**Default Models:**

| Function | Config Key | Default Model |
|----------|-----------|---------------|
| Translation | `SILICON_FLOW_MODEL` | `tencent/Hunyuan-MT-7B` |
| Markdown Layout | `SILICON_FLOW_MODEL_LAYOUT` | `Qwen/Qwen3-32B` |
| Glossary Extraction | `SILICON_FLOW_MODEL_GLOSSARY` | `Qwen/Qwen3-32B` |
| LLM OCR | `SILICON_FLOW_OCR_LLM_MODEL` | `deepseek-ai/DeepSeek-OCR` |

**Extra Request Parameters (`SILICON_FLOW_EXTRA_BODY`):**

```python
{
    "enable_thinking": False
}
```

### 7.3 Baidu Qianfan

| Item | Description |
|------|-------------|
| **Purpose** | Translation, semantic analysis, glossary extraction, LLM OCR, Markdown layout |
| **API Format** | OpenAI-compatible API (`/v2/chat/completions`) |
| **API URL** | `https://qianfan.baidubce.com/v2` |
| **Authentication** | Bearer Token (`QIANFAN_API_KEY`) |

**Default Models:**

| Function | Config Key | Default Model |
|----------|-----------|---------------|
| Translation | `QIANFAN_MODEL` | `Qwen3-32B` |
| Markdown Layout | `QIANFAN_MODEL_LAYOUT` | `Qwen3-32B` |
| Glossary Extraction | `QIANFAN_MODEL_GLOSSARY` | `Qwen3-32B` |
| LLM OCR | `QIANFAN_OCR_LLM_MODEL` | `DeepSeek-OCR` |

**Extra Request Parameters (`QIANFAN_EXTRA_BODY`):**

```python
{
    "enable_thinking": False
}
```

### 7.4 PaddleOCR

| Item | Description |
|------|-------------|
| **Purpose** | Local OCR engine for text, table, and formula recognition in scanned PDFs |
| **Version** | PP-StructureV3 |
| **Execution Mode** | Subprocess (managed by `ocr_worker.py`), with heartbeat detection, timeout, and retry support |
| **Dependencies** | `paddlepaddle` / `paddlepaddle-gpu` + `paddleocr` |
| **GPU Support** | macOS defaults to CPU; other platforms default to GPU (configurable via `OCR_USE_GPU`) |

**Key Features:**

- Layout analysis: Identifies text regions, table regions, and image regions
- Formula recognition: Recognizes mathematical formulas and converts them to LaTeX format
- Table recognition: Identifies table structures and extracts cells
- Dynamic parameter adjustment: Automatically adjusts OCR parameters based on system memory and CPU (`OCR_DYNAMIC_PARAMS`)
- Three-layer protection mechanism: Heartbeat timeout, total time limit, and progress stall detection
