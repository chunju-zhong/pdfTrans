# pdfTrans Code Wiki

> A structured, comprehensive guide to the pdfTrans codebase: architecture, modules, key classes/functions, dependencies, and run instructions.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [System Architecture](#3-system-architecture)
4. [Directory Structure](#4-directory-structure)
5. [Module Responsibilities](#5-module-responsibilities)
6. [Key Classes & Functions](#6-key-classes--functions)
7. [Data Flow & Pipelines](#7-data-flow--pipelines)
8. [Data Models](#8-data-models)
9. [Configuration System](#9-configuration-system)
10. [External Dependencies](#10-external-dependencies)
11. [Running the Project](#11-running-the-project)
12. [Testing](#12-testing)

---

## 1. Project Overview

**pdfTrans** is a PDF document translation tool that supports three independent invocation methods:

- **Web UI** (Flask app at [app.py](file:///Users/chunju/work/pdfTrans/app.py))
- **CLI** (argparse-based entry at [cli.py](file:///Users/chunju/work/pdfTrans/cli.py))
- **AI IDE Skill** (invoked through `SKILL.md` for Trae / Claude Code)

### Core Capabilities

| Capability | Description |
|------------|-------------|
| PDF Text Extraction | Extract text blocks, tables, images, style info via PyMuPDF |
| OCR Recognition | Two engines: PaddleOCR (local) + LLM OCR (cloud, DeepSeek-OCR) |
| Multi-Translation API | aiping, SiliconFlow, Baidu Qianfan (all OpenAI-compatible) |
| Multi-Format Output | PDF (preserving layout), DOCX, Markdown (with chapter split) |
| Glossary Extraction | Auto-extract domain terminology from PDF |
| Semantic Merging | Rule-based or LLM-judged merging of fragmented blocks |
| Chapter Identification | Build chapter tree from PDF bookmarks |
| Supported Languages | 9 languages: zh, en, ja, ko, fr, de, es, ru, bo |

---

## 2. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.9+ |
| Web Framework | Flask | 3.0+ |
| PDF Processing | PyMuPDF (fitz) | 1.23+ |
| Table Extraction | camelot-py[cv], opencv-python | - |
| OCR Engine | PaddleOCR (PP-StructureV3) | 3.0+ |
| Deep Learning | PaddlePaddle | 3.0+ (CPU/GPU auto) |
| Word Generation | python-docx | - |
| API Client | openai (Python SDK) | - |
| Testing | pytest | - |
| Version Control | Git + Gitee/GitHub | - |

---

## 3. System Architecture

The project follows a **three-layer architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Entry Layer                               │
│   Flask Web (app.py)  │  CLI (cli.py)  │  AI IDE Skill (SKILL.md)│
└────────────┬────────────────┬────────────────────┬────────────────┘
             │                 │                    │
             ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Service Orchestration Layer                     │
│  TranslationService  │  GlossaryService  │  TaskService         │
└────────────┬────────────────┬────────────────────┬───────────────┘
             │                 │                    │
             ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Module Layer                             │
│  PdfExtractor  │  OCR Engines  │  Translators  │  Generators   │
│  SemanticAnalyzer │ ChapterIdentifier │ GlossaryExtractor     │
└─────────────────────────────────────────────────────────────────┘
```

### Inter-Layer Call Relationships

- Entry Layer → Service Layer → Core Module Layer
- `app.py` / `cli.py` / `SKILL.md` → `TranslationService` / `GlossaryService`
- `TranslationService` → `PdfExtractor` / `Translators` / `Generators` / `SemanticAnalyzer`
- `TranslationService` / `GlossaryService` → `TaskService` (lifecycle management)

---

## 4. Directory Structure

```
pdfTrans/
├── app.py                          # Flask Web entry (HTTP APIs)
├── cli.py                          # CLI entry (argparse subcommands)
├── config.py                       # Config class — loads .env
├── SKILL.md                        # AI IDE Skill definition
├── setup.py                         # pip install -e . entry
├── environment.yml                 # Conda environment
├── install_paddle.sh               # PaddleOCR install script
│
├── models/                         # Data model layer
│   ├── copyable.py                 # CopyableMixin base
│   ├── text_block.py               # TextBlock
│   ├── extraction.py               # PdfPage / PdfCell / PdfTable / PdfImage / PdfExtraction
│   ├── merged_block.py             # MergedBlock
│   ├── task.py                     # Task (async task model)
│   ├── phase_config.py             # PHASE_CONFIG / GLOSSARY_PHASE_CONFIG
│   └── result_types.py             # TruncationInfo / Result / OpenAIResult / TranslationResult / MarkdownResult
│
├── modules/                        # Core module layer
│   ├── pdf_extractor.py            # PdfExtractor (PyMuPDF-based)
│   ├── pdf_generator.py            # PdfGenerator (translated PDF)
│   ├── pdf_text_renderer.py        # PDF text rendering helper
│   ├── pdf_table_renderer.py       # PDF table rendering helper
│   ├── docx_generator.py           # DocxGenerator
│   ├── markdown_generator.py       # MarkdownGenerator (with LLM layout)
│   ├── translator.py               # Translator base class
│   ├── aiping_translator.py        # AipingTranslator
│   ├── silicon_flow_translator.py  # SiliconFlowTranslator
│   ├── qianfan_translator.py       # QianfanTranslator
│   ├── semantic_analyzer.py        # SemanticAnalyzer base
│   ├── aiping_semantic_analyzer.py # AipingSemanticAnalyzer
│   ├── semantic_analyzer_factory.py # SemanticAnalyzerFactory
│   ├── chapter_identifier.py       # ChapterIdentifier + Chapter
│   ├── glossary_extractor.py       # GlossaryExtractor base + factory
│   ├── llm_error_handler.py        # classify_llm_error()
│   ├── extractors/                 # PDF extraction sub-module
│   │   ├── coordinate_utils.py
│   │   ├── page_utils.py
│   │   ├── style_analyzer.py
│   │   ├── table_processor.py
│   │   └── text_analyzer.py
│   └── ocr/                        # OCR sub-module
│       ├── base.py                 # OcrExtractor (ABC)
│       ├── factory.py              # create_ocr_extractor()
│       ├── paddle_extractor.py     # PaddleOcrExtractor
│       ├── llm_extractor.py        # LlmOcrExtractor (DeepSeek-OCR)
│       ├── llm_response_parser.py # LlmOcrResponseParser
│       ├── llm_table_parser.py    # LlmTableParser
│       ├── ocr_worker.py           # Subprocess manager
│       └── system_profiler.py      # OcrParameterCalculator
│
├── services/                       # Service orchestration layer
│   ├── translation_service.py      # TranslationService (core)
│   ├── translation_content.py      # TranslationContentTranslator
│   ├── translation_extractor.py    # TranslationExtractor
│   ├── translation_output.py       # TranslationOutputGenerator
│   ├── translation_table.py        # TranslationTableHandler
│   ├── task_service.py              # TaskService
│   └── glossary_service.py         # GlossaryService
│
├── cli/                            # CLI subcommand handlers
│   ├── translate_command.py
│   ├── glossary_command.py
│   ├── list_languages_command.py
│   └── progress_display.py
│
├── prompts/                        # Prompt rule system
│   ├── rule_registry.py            # PromptRuleRegistry (singleton)
│   └── language_rules/
│       ├── base.py
│       └── bo_to_zh.py             # Tibetan→Chinese specific rules
│
├── utils/
│   ├── file_utils.py
│   ├── logging_config.py
│   └── text_processing.py          # Semantic merge / split logic
│
├── templates/                      # Flask HTML templates
├── static/                          # CSS / JS assets
├── tests/                          # pytest test suite
└── docs/                           # Documentation
```

---

## 5. Module Responsibilities

### 5.1 Entry Layer

| File | Responsibility |
|------|----------------|
| [app.py](file:///Users/chunju/work/pdfTrans/app.py) | Flask app; HTTP routes for `/translate`, `/progress/<id>`, `/cancel/<id>`, `/download/<filename>`, `/extract_glossary`, `/get_pdf_pages`. Spawns async translation threads. |
| [cli.py](file:///Users/chunju/work/pdfTrans/cli.py) | argparse CLI with `translate`, `glossary`, `list-languages` subcommands; routes to handlers in `cli/`. |
| [SKILL.md](file:///Users/chunju/work/pdfTrans/SKILL.md) | AI IDE Skill descriptor; Trae/Claude Code invoke CLI on natural language requests. |

### 5.2 Service Orchestration Layer

| Class | File | Responsibility |
|-------|------|----------------|
| `TranslationService` | [services/translation_service.py](file:///Users/chunju/work/pdfTrans/services/translation_service.py) | Orchestrates the full translation pipeline; delegates to 4 sub-modules. Provides async `process_translation()` (Web) and sync `process_translation_sync()` (CLI). |
| `TranslationExtractor` | [services/translation_extractor.py](file:///Users/chunju/work/pdfTrans/services/translation_extractor.py) | Sub-module: PDF content extraction (text/tables/images/chapters). |
| `TranslationContentTranslator` | [services/translation_content.py](file:///Users/chunju/work/pdfTrans/services/translation_content.py) | Sub-module: text translation (parallel via ThreadPoolExecutor). |
| `TranslationTableHandler` | [services/translation_table.py](file:///Users/chunju/work/pdfTrans/services/translation_table.py) | Sub-module: table cell translation, row-by-row batching. |
| `TranslationOutputGenerator` | [services/translation_output.py](file:///Users/chunju/work/pdfTrans/services/translation_output.py) | Sub-module: PDF/DOCX/Markdown output generation. |
| `TaskService` | [services/task_service.py](file:///Users/chunju/work/pdfTrans/services/task_service.py) | Task lifecycle: create / get / cancel / update_progress / set_result / set_error. In-memory store. |
| `GlossaryService` | [services/glossary_service.py](file:///Users/chunju/work/pdfTrans/services/glossary_service.py) | Glossary extraction workflow: PDF text extraction → parallel term extraction. |

### 5.3 Core Module Layer

#### PDF Extraction

| Class | File | Responsibility |
|-------|------|----------------|
| `PdfExtractor` | [modules/pdf_extractor.py](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py) | PyMuPDF-based extraction: text blocks, tables (camelot or pymupdf), images. Branches to OCR when `ocr_mode=True`. |
| `ChapterIdentifier` | [modules/chapter_identifier.py](file:///Users/chunju/work/pdfTrans/modules/chapter_identifier.py) | Builds chapter tree from PDF bookmarks; assigns chapter_id/title/level to text blocks, tables, images. |

##### extractors sub-module

| File | Functions |
|------|-----------|
| [coordinate_utils.py](file:///Users/chunju/work/pdfTrans/modules/extractors/coordinate_utils.py) | `convert_pdf_to_pymupdf_coords`, `calculate_cell_bbox`, `calculate_row_heights`, `calculate_col_widths` |
| [page_utils.py](file:///Users/chunju/work/pdfTrans/modules/extractors/page_utils.py) | `process_page_numbers`, `validate_page_number`, `get_pages_for_processing`, `create_pages_param` |
| [style_analyzer.py](file:///Users/chunju/work/pdfTrans/modules/extractors/style_analyzer.py) | `analyze_text_block_style`, `find_matching_block`, `calculate_main_style`, `update_text_block_style` |
| [text_analyzer.py](file:///Users/chunju/work/pdfTrans/modules/extractors/text_analyzer.py) | `mark_non_body_text`, `identify_header_footer`, `identify_page_numbers`, `calculate_text_similarity` |
| [table_processor.py](file:///Users/chunju/work/pdfTrans/modules/extractors/table_processor.py) | `extract_tables_by_camelot`, `extract_tables_by_pymupdf`, `get_table_bboxes_by_page`, `process_table_data` |

#### OCR Engines

| Class | File | Responsibility |
|-------|------|----------------|
| `OcrExtractor` (ABC) | [modules/ocr/base.py](file:///Users/chunju/work/pdfTrans/modules/ocr/base.py) | Abstract base; defines `extract_from_pdf(pdf_path, pages, temp_images_dir)`. |
| — | [modules/ocr/factory.py](file:///Users/chunju/work/pdfTrans/modules/ocr/factory.py) | `create_ocr_extractor(ocr_type, **kwargs)` factory; supports `'paddleocr'`, `'llm'`. |
| `PaddleOcrExtractor` | [modules/ocr/paddle_extractor.py](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py) | PP-StructureV3 local engine; layout analysis, table grid, formula detection. |
| `LlmOcrExtractor` | [modules/ocr/llm_extractor.py](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_extractor.py) | DeepSeek-OCR cloud engine; blank page detection, timeout handling. |
| `LlmOcrResponseParser` | [modules/ocr/llm_response_parser.py](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_response_parser.py) | Three-stage response parsing (`<|ref|>` / JSON / Markdown). |
| `LlmTableParser` | [modules/ocr/llm_table_parser.py](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_table_parser.py) | Table layout (row-height-priority iterative optimization). |
| `OcrWorker` | [modules/ocr/ocr_worker.py](file:///Users/chunju/work/pdfTrans/modules/ocr/ocr_worker.py) | Subprocess isolation with heartbeat, timeout, retry, parameter degradation. |
| `OcrParameterCalculator` | [modules/ocr/system_profiler.py](file:///Users/chunju/work/pdfTrans/modules/ocr/system_profiler.py) | 5-level memory tiering (minimal→unlimited); auto-selects model scale. |

#### Translators

| Class | File | Responsibility |
|-------|------|----------------|
| `Translator` (base) | [modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py) | Defines `translate()`, `batch_translate()`, `format_blocks()`, prompt builders. |
| `AipingTranslator` | [modules/aiping_translator.py](file:///Users/chunju/work/pdfTrans/modules/aiping_translator.py) | aiping platform; passes `AIPING_EXTRA_BODY`. |
| `SiliconFlowTranslator` | [modules/silicon_flow_translator.py](file:///Users/chunju/work/pdfTrans/modules/silicon_flow_translator.py) | SiliconFlow platform. |
| `QianfanTranslator` | [modules/qianfan_translator.py](file:///Users/chunju/work/pdfTrans/modules/qianfan_translator.py) | Baidu Qianfan; passes both `enable_thinking` and `thinking.type=disabled`. |

#### Semantic Analyzer

| Class | File | Responsibility |
|-------|------|----------------|
| `SemanticAnalyzer` (base) | [modules/semantic_analyzer.py](file:///Users/chunju/work/pdfTrans/modules/semantic_analyzer.py) | Base class for LLM-based semantic merge judgment. |
| `AipingSemanticAnalyzer` | [modules/aiping_semantic_analyzer.py](file:///Users/chunju/work/pdfTrans/modules/aiping_semantic_analyzer.py) | aiping-specific implementation. |
| `SemanticAnalyzerFactory` | [modules/semantic_analyzer_factory.py](file:///Users/chunju/work/pdfTrans/modules/semantic_analyzer_factory.py) | `create_analyzer(analyzer_type, ...)` factory. |

#### Output Generators

| Class | File | Responsibility |
|-------|------|----------------|
| `PdfGenerator` | [modules/pdf_generator.py](file:///Users/chunju/work/pdfTrans/modules/pdf_generator.py) | Generates translated PDF overlaying original layout. |
| `PdfTextRenderer` | [modules/pdf_text_renderer.py](file:///Users/chunju/work/pdfTrans/modules/pdf_text_renderer.py) | PDF text rendering helper (split from PdfGenerator). |
| `PdfTableRenderer` | [modules/pdf_table_renderer.py](file:///Users/chunju/work/pdfTrans/modules/pdf_table_renderer.py) | PDF table rendering helper. |
| `DocxGenerator` | [modules/docx_generator.py](file:///Users/chunju/work/pdfTrans/modules/docx_generator.py) | Word document generation preserving fonts/styles. |
| `MarkdownGenerator` | [modules/markdown_generator.py](file:///Users/chunju/work/pdfTrans/modules/markdown_generator.py) | Markdown generation with LLM-based layout; supports chapter split as ZIP. |

#### Other Modules

| Class/Function | File | Responsibility |
|----------------|------|----------------|
| `GlossaryExtractor` (ABC) + `create_glossary_extractor()` | [modules/glossary_extractor.py](file:///Users/chunju/work/pdfTrans/modules/glossary_extractor.py) | Domain terminology extraction; supports aiping / silicon_flow / qianfan. |
| `classify_llm_error()` | [modules/llm_error_handler.py](file:///Users/chunju/work/pdfTrans/modules/llm_error_handler.py) | Maps OpenAI exceptions to user-friendly Chinese messages. Categories: auth, rate_limit, bad_request_max_tokens, timeout, connection, server_error. |

### 5.4 Prompt Rule System

| Class | File | Responsibility |
|-------|------|----------------|
| `PromptRule` (dataclass) | [prompts/rule_registry.py](file:///Users/chunju/work/pdfTrans/prompts/rule_registry.py) | One language-specific rule (task_type, source/target lang, priority, content). |
| `PromptRuleRegistry` (singleton) | [prompts/rule_registry.py](file:///Users/chunju/work/pdfTrans/prompts/rule_registry.py) | `register()` / `get_rules()` / `merge_into_prompt()`; auto-discovered via `prompts/language_rules/__init__.py`. |

Task types: `translation`, `glossary`, `semantic`, `ocr`, `layout`, `*` (universal).

---

## 6. Key Classes & Functions

### 6.1 `TranslationService` ([services/translation_service.py](file:///Users/chunju/work/pdfTrans/services/translation_service.py))

```python
class TranslationService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=config.MAX_WORKERS)
        self.extractor = TranslationExtractor(self.executor)
        self.content_translator = TranslationContentTranslator(self.executor)
        self.table_handler = TranslationTableHandler(self.executor)
        self.output_generator = TranslationOutputGenerator()

    # Web entrypoint (async)
    def process_translation(self, task, input_filepath, source_lang, target_lang,
                            translator_type, unique_id, filename, ...): ...

    # CLI entrypoint (sync, returns output_files)
    def process_translation_sync(self, task, input_filepath, ..., is_cli=False,
                                  output_path=None, tmp_dir=None): ...

    def get_translator(self, translator_type, model=None) -> Translator: ...
    def get_semantic_analyzer(self, analyzer_type, model=None) -> SemanticAnalyzer: ...
    def parse_page_range(self, page_range_str, total_pages) -> Set[int]: ...
```

Module-level singleton: `translation_service = TranslationService()`.

### 6.2 `Task` ([models/task.py](file:///Users/chunju/work/pdfTrans/models/task.py))

```python
class Task(CopyableMixin):
    # status: pending | processing | completed | error
    # task_type: translation | glossary
    # phase_config: PHASE_CONFIG or GLOSSARY_PHASE_CONFIG
    def update_phase_progress(self, phase, phase_percent, message=None) -> bool: ...
    def set_status(self, status): ...
    def set_result(self, result_file) -> bool: ...
    def set_error(self, error_message): ...
    def cancel(self): ...
    def is_canceled(self) -> bool: ...
```

Thread-safe (uses `threading.RLock`); used by both Web and CLI flows.

### 6.3 `PdfExtractor` ([modules/pdf_extractor.py](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py))

```python
class PdfExtractor:
    def __init__(self, pdf_path=None, table_extractor='pymupdf',
                 ocr_mode=False, ocr_engine='paddleocr', ocr_lang='ch',
                 translator_type='aiping', source_lang='en', ocr_llm_model=None): ...

    def extract(self) -> PdfExtraction: ...      # Main entry
    def extract_tables(self, pages=None): ...     # Returns (tables, bboxes, cell_bboxes)
    def get_metadata(self) -> dict: ...
```

When `ocr_mode=True`, delegates to `OcrExtractor` via the factory.

### 6.4 `Translator` (base) ([modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py))

```python
class Translator:
    def translate(self, text, source_lang, target_lang, doc_type, glossary) -> TranslationResult:
        if source_lang == target_lang:
            return TranslationResult(content=text, ...)  # No-op
        raise NotImplementedError

    def batch_translate(self, texts, source_lang, target_lang, ...) -> list[TranslationResult]: ...
    def format_blocks(self, translated_texts, target_lang="zh") -> list[str]: ...

    def _generate_system_prompt(self, doc_type, source_lang_name, target_lang_name,
                                glossary, source_lang_code=None, target_lang_code=None) -> str: ...
    def _generate_user_prompt(self, source_lang_name, target_lang_name, doc_type, text) -> str: ...
```

Subclasses (`AipingTranslator`, `SiliconFlowTranslator`, `QianfanTranslator`) override the API call logic and the `_get_format_api_kwargs()` hook to inject `extra_body` parameters.

### 6.5 `OcrExtractor` (ABC) ([modules/ocr/base.py](file:///Users/chunju/work/pdfTrans/modules/ocr/base.py))

```python
class OcrExtractor(ABC):
    @abstractmethod
    def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None) -> PdfExtraction: ...
```

Returns a `PdfExtraction` with the same structure as `PdfExtractor.extract()`, allowing seamless integration into the translation pipeline.

### 6.6 Semantic Merge Functions ([utils/text_processing.py](file:///Users/chunju/work/pdfTrans/utils/text_processing.py))

```python
def merge_semantic_blocks(text_blocks, progress_callback=None) -> tuple[list[MergedBlock], list]: ...
def merge_semantic_blocks_with_llm(text_blocks, semantic_analyzer, ...) -> tuple[list[MergedBlock], list]: ...
def merge_semantic_blocks_with_llm_two_phase(text_blocks, semantic_analyzer, ...) -> tuple[list[MergedBlock], list]: ...
def split_translated_result(merged_block, translated_text, original_blocks) -> list[TextBlock]: ...
```

### 6.7 `classify_llm_error()` ([modules/llm_error_handler.py](file:///Users/chunju/work/pdfTrans/modules/llm_error_handler.py))

```python
def classify_llm_error(e: Exception) -> dict:
    # Returns: { category, user_message, is_retryable, original_message }
    # Categories: auth, rate_limit, bad_request_max_tokens, bad_request,
    #             timeout, connection, server_error, unknown
```

---

## 7. Data Flow & Pipelines

### 7.1 Translation Pipeline — 7 Phases

Defined in [models/phase_config.py](file:///Users/chunju/work/pdfTrans/models/phase_config.py) `PHASE_CONFIG`:

| # | Phase ID | Progress | Description |
|---|----------|----------|-------------|
| 1 | `init` | 0% – 5% | Save file, create task |
| 2 | `extraction` | 5% – 40% | Extract text blocks, tables, images (PyMuPDF or OCR) |
| 3 | `semantic_merge` | 40% – 50% | Merge fragmented blocks (rule-based or LLM) |
| 4 | `translation` | 50% – 85% | Parallel translation of merged text blocks |
| 5 | `table_translation` | 85% – 92% | Batch-translate table cells row by row |
| 6 | `generation` | 92% – 98% | Generate PDF / DOCX / Markdown files |
| 7 | `clean` | 98% – 100% | Delete uploaded file and temporary images |

### 7.2 Glossary Extraction Pipeline — 3 Phases

Defined in `GLOSSARY_PHASE_CONFIG`:

| # | Phase ID | Progress | Description |
|---|----------|----------|-------------|
| 1 | `init` | 0% – 5% | Save file, create task |
| 2 | `pdf_extraction` | 5% – 30% | Extract text from all PDF pages |
| 3 | `term_extraction` | 30% – 100% | Parallel LLM calls for terminology |

### 7.3 Data Transformation Pipeline

```
PDF File
   │
   ▼  PdfExtractor.extract()  (or OcrExtractor.extract_from_pdf())
PdfExtraction
   ├── pages: [PdfPage]
   │     └── text_blocks: [TextBlock]      ← Raw blocks with style & position
   ├── tables: [PdfTable]
   │     └── cells: [[PdfCell]]
   └── images: [PdfImage]
   │
   ▼  merge_semantic_blocks()  / merge_semantic_blocks_with_llm()
[MergedBlock]                              ← Merged semantic blocks
   │
   ▼  Translator.translate()  (parallel, ThreadPoolExecutor)
[TranslationResult]
   │
   ▼  split_translated_result()
[TextBlock]  (translated, preserving original style/position)
   │
   ▼  PdfGenerator / DocxGenerator / MarkdownGenerator
PDF / DOCX / Markdown file(s)
```

### 7.4 Web Request Lifecycle

```
1. POST /translate
   ├── Save file to UPLOAD_FOLDER/{uuid}_{filename}
   ├── task_service.create_task(task_id, filename)
   ├── threading.Thread(target=translation_service.process_translation, ...)
   └── Return task_id

2. GET /progress/<task_id>  (poll from frontend)
   └── task_service.get_task(task_id).to_dict()

3. POST /cancel/<task_id>
   └── task_service.cancel_task(task_id) → task.cancel()

4. GET /download/<filename>  → render download.html
5. GET /download_file/<filename>  → send_from_directory(OUTPUT_FOLDER, filename)
```

### 7.5 CLI Flow

```
cli.py main() → args.command
   ├── translate  → cli/translate_command.py translate_handler(args)
   │      ├── Validate input file & glossary
   │      ├── Create Task object
   │      ├── translation_service.process_translation_sync(task, ...)
   │      └── ProgressDisplay callback updates terminal
   ├── glossary   → cli/glossary_command.py glossary_handler(args)
   └── list-languages → cli/list_languages_command.py
```

---

## 8. Data Models

### 8.1 Model Hierarchy

```
CopyableMixin  (models/copyable.py — provides copy() + to_dict/from_dict)
   ├── TextBlock           (text_block.py)
   ├── PdfPage             (extraction.py)
   ├── PdfCell             (extraction.py)
   ├── PdfTable            (extraction.py)
   ├── PdfImage            (extraction.py)
   ├── PdfExtraction       (extraction.py)
   ├── MergedBlock         (merged_block.py)
   ├── Task                (task.py)
   ├── TruncationInfo      (result_types.py)
   ├── Result              (result_types.py)
   │    └── OpenAIResult
   │         ├── TranslationResult
   │         └── MarkdownResult
   └── Chapter             (chapter_identifier.py)
```

### 8.2 Key Models

#### TextBlock — Text Block

| Field | Type | Description |
|-------|------|-------------|
| `block_no` | int | Block sequence number |
| `block_text` | str | Text content |
| `block_bbox` | tuple | Bounding box (x0, y0, x1, y1) |
| `block_type` | int | Block type |
| `page_num` | int | Page number |
| `font`, `font_size`, `color`, `flags` | - | Style info |
| `bold`, `italic`, `underline`, `strikethrough` | bool | Style flags (parsed from `flags`) |
| `is_body_text`, `is_formula` | bool | Classification flags |
| `alignment` | int | 0=left, 1=center, 2=right |
| `chapter_id`, `chapter_title`, `chapter_level`, `chapter_number` | - | Chapter info |

#### PdfExtraction — Extraction Result

| Field | Type | Description |
|-------|------|-------------|
| `total_pages` | int | Total PDF pages |
| `pages` | list[PdfPage] | Per-page text blocks |
| `tables` | list[PdfTable] | All tables |
| `images` | list[PdfImage] | All extracted images |

#### MergedBlock — Merged Semantic Block

| Field | Type | Description |
|-------|------|-------------|
| `block_text` | str | Merged text |
| `original_blocks` | list[TextBlock] | Original blocks (kept for layout reconstruction) |
| `max_width`, `max_height` | float | Merged dimensions |
| `is_formula` | bool | Auto-detected formula flag |
| `font`, `font_size`, `bold`, `italic`, `color`, `flags`, `page_num` | - | Style (from first original block) |

#### Task — Async Task

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | str | Unique ID |
| `filename` | str | Original filename |
| `status` | str | pending / processing / completed / error |
| `progress` | int | 0-100 overall |
| `current_phase` | str | Phase ID |
| `phase_config` | dict | Phase → range mapping |
| `result_file`, `attachments` | - | Output files |
| `warnings`, `error`, `canceled` | - | Status fields |
| `lock` | RLock | Thread-safe lock |

#### TranslationResult

```python
TranslationResult(OpenAIResult):
    content: str              # Translated text
    token_usage: dict
    finish_reason: str        # "stop" or "length"
    truncation_info: TruncationInfo
        truncated: bool       # True if finish_reason == "length"
```

---

## 9. Configuration System

Configuration is managed by the `Config` class in [config.py](file:///Users/chunju/work/pdfTrans/config.py). It loads environment variables from `.env` via `python-dotenv`.

### Loading Mechanism

```python
from dotenv import load_dotenv
load_dotenv()

class Config:
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024   # Static class-level constant
    SUPPORTED_LANGUAGES = { ... }            # Static class-level constant

    def __init__(self):
        self._load()                         # Read env vars as instance attributes

    def _load(self):
        self.SECRET_KEY = os.environ.get('SECRET_KEY')   # Required
        # ... all env-dependent attributes
```

- Static constants (e.g., `MAX_CONTENT_LENGTH`, `SUPPORTED_LANGUAGES`, `*_EXTRA_BODY`) stay at class level
- Env-dependent attributes are set as instance attributes (lazy evaluation)
- `SECRET_KEY` is **required** — raises `RuntimeError` if missing
- Supports runtime reload: call `config._load()` after modifying environment variables

Module-level singleton: `config = Config()`.

### Configuration Categories

| Category | Examples |
|----------|---------|
| Basic | `SECRET_KEY`, `DEBUG`, `UPLOAD_FOLDER`, `OUTPUT_FOLDER` |
| API Credentials | `AIPING_API_KEY`, `SILICON_FLOW_API_KEY`, `QIANFAN_API_KEY` |
| Models | `AIPING_MODEL`, `SILICON_FLOW_MODEL_LAYOUT`, `QIANFAN_OCR_LLM_MODEL`, ... |
| Thread Pool | `MAX_WORKERS=8`, `TRANSLATION_BATCH_SIZE=10`, `MERGE_MAX_WORKERS=5` |
| OCR | `USE_OCR=false`, `OCR_ENGINE`, `OCR_USE_GPU`, `OCR_PADDLE_DPI=120` |
| OCR Timeout/Retry | `OCR_HEARTBEAT_TIMEOUT`, `OCR_MAX_RETRIES=2`, `OCR_RETRY_BACKOFF=5.0` |
| LLM OCR | `OCR_LLM_MAX_TOKENS=8192`, `OCR_LLM_TEMPERATURE=0.1`, `OCR_LLM_DPI=150` |
| Per-Module API | `TRANSLATION_TEMPERATURE=0.1`, `GLOSSARY_TEMPERATURE=0.3`, `LAYOUT_TEMPERATURE=0.1` |

See [docs/ARCHITECTURE.md](file:///Users/chunju/work/pdfTrans/docs/ARCHITECTURE.md) §6 for the complete reference table.

---

## 10. External Dependencies

### Translation API Providers

All three use OpenAI-compatible `/v1/chat/completions` (or `/v2/` for Qianfan) endpoints with Bearer Token auth.

| Provider | URL | Default Translation Model |
|----------|-----|---------------------------|
| aiping | `https://aiping.cn/api/v1` | `Qwen3-32B` |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `tencent/Hunyuan-MT-7B` |
| Baidu Qianfan | `https://qianfan.baidubce.com/v2` | `Qwen3-32B` |

### OCR Engines

| Engine | Type | Notes |
|--------|------|-------|
| PaddleOCR (PP-StructureV3) | Local | Requires `paddlepaddle`/`paddlepaddle-gpu` + `paddleocr`. macOS defaults to CPU. |
| LLM OCR (DeepSeek-OCR) | Cloud | Uses translation service API Key; no PaddlePaddle needed. |

### Other Dependencies

- **PyMuPDF (fitz)** — PDF text extraction & generation
- **camelot-py[cv]** + **opencv-python** — Alternative table extraction
- **python-docx** — Word generation
- **openai (Python SDK)** — API client for all translation platforms
- **python-dotenv** — `.env` loading
- **Flask** — Web framework
- **LaTeX (optional)** — High-quality formula rendering (falls back to matplotlib mathtext)

---

## 11. Running the Project

### 11.1 Installation

```bash
# 1. Clone
git clone https://gitee.com/chunju/pdfTrans.git
cd pdfTrans

# 2. Create conda env
conda env create -f environment.yml
conda activate pdfTrans

# 3. Configure environment
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY and one of AIPING_API_KEY / SILICON_FLOW_API_KEY / QIANFAN_API_KEY

# 4. Install Python deps
pip install -r requirements.txt

# 5. (Optional) Install PaddlePaddle for OCR
bash install_paddle.sh
# Or manually: pip install paddlepaddle>=3.0.0   (CPU)
#              pip install paddlepaddle-gpu>=3.0.0  (GPU)

# 6. (Optional) Install LaTeX for high-quality formula rendering
# macOS:    brew install --cask mactex
# Linux:    sudo apt-get install texlive-full
```

### 11.2 Web UI

```bash
python app.py
# Open http://localhost:5000

# Custom port
python app.py --port 8080
```

Key endpoints:

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/` | Home page (translation form) |
| POST | `/translate` | Start async translation task |
| GET | `/progress/<task_id>` | Poll task progress |
| POST | `/cancel/<task_id>` | Cancel task |
| GET | `/download/<filename>` | Download page |
| GET | `/download_file/<filename>` | File download |
| POST | `/extract_glossary` | Start async glossary extraction |
| GET | `/glossary_progress/<task_id>` | Poll glossary progress |
| POST | `/glossary_cancel/<task_id>` | Cancel glossary task |
| POST | `/get_pdf_pages` | Get total PDF page count |

### 11.3 CLI

```bash
# Install as CLI tool
pip install -e .

# Or use directly without install
python cli.py --help

# Common commands
pdftrans translate document.pdf -o translated.pdf
pdftrans translate document.pdf -s en -t zh -T silicon_flow -o out.pdf
pdftrans translate document.pdf --pages "1-10,15,20-25" -o out.pdf
pdftrans translate document.pdf -f docx -o output.docx
pdftrans translate document.pdf -f markdown --chapter-split -o output/
pdftrans translate document.pdf --ocr --ocr-engine llm -o out.pdf
pdftrans translate document.pdf -m -l -f docs -o out.pdf    # semantic merge + LLM
pdftrans translate document.pdf -g glossary.txt -o out.pdf

pdftrans glossary document.pdf -o glossary.txt
pdftrans list-languages
```

**Translate command options:**

| Flag | Description |
|------|-------------|
| `-o, --output` | Output path (auto-generated if omitted) |
| `-s, --source` | Source language code (default: `en`) |
| `-t, --target` | Target language code (default: `zh`) |
| `-T, --translator` | `aiping` / `silicon_flow` / `qianfan` |
| `-p, --pages` | Page range like `"1-5,7,9-10"` |
| `-f, --format` | `pdf` / `docx` / `markdown` / `pdf_docx` / `all` |
| `-g, --glossary` | Glossary file path |
| `-d, --doc-type` | Document domain (default: `AI技术`) |
| `-m, --semantic-merge` | Enable semantic merge |
| `-l, --llm-merge` | Use LLM for semantic judgment |
| `-c, --chapter-split` | Split Markdown by chapter |
| `--ocr` | Enable OCR extraction |
| `--ocr-engine` | `paddleocr` (local) or `llm` (cloud) |
| `--ocr-lang` | OCR recognition language |
| `--translation-model` | Override translation model |
| `--layout-model` | Override Markdown layout model |
| `--glossary-model` | Override glossary extraction model |
| `--ocr-llm-model` | Override LLM OCR model |

### 11.4 AI IDE Skill

Place the `pdfTrans` repository under your project's `.trae/skills/pdftrans/` directory. Trae detects `SKILL.md` automatically and invokes CLI commands based on natural language requests like "Translate this PDF to Chinese".

---

## 12. Testing

The project uses `pytest`. Test files live under [tests/](file:///Users/chunju/work/pdfTrans/tests/).

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=term-missing

# Specific test file
pytest tests/test_translation_service.py -v
```

Test configuration: [pytest.ini](file:///Users/chunju/work/pdfTrans/pytest.ini). Shared fixtures in [tests/conftest.py](file:///Users/chunju/work/pdfTrans/tests/conftest.py).

### Test Coverage Areas

- `test_pdf_extractor.py` — PDF text/table/image extraction
- `test_translation_service.py` — Translation service orchestration
- `test_semantic_merge.py` — Semantic merge logic (rule-based + LLM)
- `test_ocr_extractor.py` — OCR engines (PaddleOCR + LLM OCR)

---

## Appendix: Conventions

### File Naming

- Python modules: `snake_case.py`
- Classes: `PascalCase` (e.g., `TranslationService`, `PdfExtractor`)
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Test files: `test_*.py`

### Error Handling

- `classify_llm_error()` ([modules/llm_error_handler.py](file:///Users/chunju/work/pdfTrans/modules/llm_error_handler.py)) maps OpenAI exceptions to user-friendly Chinese messages
- Task failures call `task.set_error(message)` and clean up temporary files
- CLI mode preserves source files on failure (`is_cli=True`)

### Immutability

Models inherit from `CopyableMixin`, providing `copy()` and `to_dict()`/`from_dict()` for safe data transformation without in-place mutation.

### Thread Safety

- `Task` uses `threading.RLock` for all state mutations
- `TranslationService` uses `ThreadPoolExecutor(max_workers=config.MAX_WORKERS)` for parallel translation
- OCR runs in subprocess (via `OcrWorker`) to isolate PaddlePaddle memory leaks

### Output Directory Convention

- Main output directory: contains final files
- `tmp/` subdirectory: contains intermediate files (Markdown, images)
- OCR temporary images are cleaned up only after **all** output files have been generated
