# pdfTrans Development Guide

## 1. Environment Requirements and Setup

### 1.1 System Requirements

- **Python**: 3.9+ (3.9 recommended, consistent with `environment.yml`)
- **Operating System**: macOS / Linux / Windows
- **Memory**: 8GB+ recommended (16GB recommended for OCR mode)
- **GPU**: Optional; NVIDIA GPU + CUDA 11.8+ can accelerate PaddleOCR

### 1.2 Conda Environment Setup

```bash
# Create conda environment using environment.yml
conda env create -f environment.yml

# Activate the environment
conda activate pdftrans
```

`environment.yml` defines the following core dependencies:

| Dependency | Install Method | Description |
|------------|---------------|-------------|
| python=3.9 | conda | Python version |
| flask | conda | Web framework |
| requests | conda | HTTP request library |
| python-dotenv | conda | Environment variable loader |
| ghostscript | conda | PDF/image processing tool |
| pymupdf | pip | PDF parsing library |
| camelot-py[cv] | pip | PDF table extraction |
| opencv-python | pip | Image processing |

### 1.3 pip Dependency Installation

If not using conda, install directly via pip:

```bash
pip install -r requirements.txt
```

Complete dependencies in `requirements.txt`:

| Dependency | Purpose |
|------------|---------|
| flask | Web service |
| pymupdf | PDF text and page extraction |
| camelot-py[cv] | PDF table extraction |
| ghostscript | Ghostscript dependency for camelot |
| opencv-python | Image processing |
| requests | HTTP requests |
| python-dotenv | .env file loading |
| openai | OpenAI-compatible API client |
| pytest | Testing framework |
| python-docx | Word document generation |
| matplotlib | Chart rendering |
| latex2mathml | LaTeX to MathML (formula rendering) |
| psutil | System resource monitoring |
| paddleocr[all]>=3.0.0 | PaddleOCR full dependencies (including PP-StructureV3) |

### 1.4 PaddlePaddle Installation

PaddlePaddle CPU and GPU versions cannot be installed simultaneously. Use the install script to select automatically:

```bash
bash install_paddle.sh
```

Script logic:
1. **macOS** → Automatically installs CPU version (macOS does not support GPU)
2. **Linux without NVIDIA GPU** → Installs CPU version
3. **Linux with NVIDIA GPU + CUDA ≥ 11.8** → Installs GPU version
4. **Linux with NVIDIA GPU + CUDA < 11.8** → Installs CPU version

Manual installation:

```bash
# CPU version
pip install "paddlepaddle>=3.0.0"

# GPU version (requires NVIDIA GPU + CUDA)
pip install "paddlepaddle-gpu>=3.0.0"
```

Verify installation:

```bash
python -c 'import paddle; print(paddle.__version__)'
```

### 1.5 .env File Configuration

```bash
# Copy from template
cp .env.example .env

# Edit configuration
vim .env
```

**Required configuration**: At least one translation service API key (`AIPING_API_KEY`, `SILICON_FLOW_API_KEY`, or `QIANFAN_API_KEY`) must be configured, along with `SECRET_KEY`.

### 1.6 Platform Notes

| Platform | Notes |
|----------|-------|
| **macOS** | PaddleOCR uses CPU by default; Intel Macs with 16GB RAM may need `OCR_SKIP_TABLE=true` to save memory |
| **Linux** | Supports GPU acceleration; requires CUDA drivers |
| **Windows** | Requires manual Ghostscript installation and PATH configuration; some path handling may need adjustment |

---

## 2. Configuration Reference

All configuration is set via the `.env` file or environment variables, loaded by the `Config` class in `config.py`.

### 2.1 Flask Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask secret key for session security | None (startup error if unset) | **Yes** |
| `DEBUG` | Debug mode | `False` | No |

### 2.2 aiping API Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AIPING_API_KEY` | aiping API key | None | Required when using aiping |
| `AIPING_API_URL` | aiping API endpoint | `https://aiping.cn/api/v1` | No |
| `AIPING_MODEL_TRANSLATION` | Translation model | `Qwen3-32B` | No |
| `AIPING_MODEL_LAYOUT` | Markdown layout model | `Qwen3-32B` | No |
| `AIPING_MODEL_GLOSSARY` | Glossary extraction model | `Qwen3-32B` | No |

### 2.3 SiliconFlow API Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SILICON_FLOW_API_KEY` | SiliconFlow API key | None | Required when using silicon_flow |
| `SILICON_FLOW_API_URL` | SiliconFlow API endpoint | `https://api.siliconflow.cn/v1` | No |
| `SILICON_FLOW_MODEL_TRANSLATION` | Translation model | `tencent/Hunyuan-MT-7B` | No |
| `SILICON_FLOW_MODEL_LAYOUT` | Markdown layout model | `Qwen/Qwen3-32B` | No |
| `SILICON_FLOW_MODEL_GLOSSARY` | Glossary extraction model | `Qwen/Qwen3-32B` | No |

### 2.4 Baidu Qianfan API Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `QIANFAN_API_KEY` | Baidu Qianfan API key | None | Required when using qianfan |
| `QIANFAN_API_URL` | Baidu Qianfan API endpoint | `https://qianfan.baidubce.com/v2` | No |
| `QIANFAN_MODEL` | Translation model | None | No |
| `QIANFAN_MODEL_LAYOUT` | Markdown layout model | None | No |
| `QIANFAN_MODEL_GLOSSARY` | Glossary extraction model | None | No |
| `QIANFAN_OCR_LLM_MODEL` | Qianfan LLM OCR model | None | No |
| `QIANFAN_EXTRA_BODY` | Qianfan API extra_body parameter (JSON) | `{}` | No |

> **Code-level default**: When the `QIANFAN_EXTRA_BODY` environment variable is not set, the code uses the class-level default `{"enable_thinking": False, "thinking": {"type": "disabled"}}`, which disables thinking for both Qwen3 series (`enable_thinking`) and GLM-4.5+/5.x series (`thinking.type`). See [ARCHITECTURE.md](ARCHITECTURE.md) Section 7.3 for details.

### 2.5 OCR Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `USE_OCR` | Enable OCR by default | `false` | No |
| `OCR_ENGINE` | OCR engine type | `paddleocr` | No |
| `OCR_LANGUAGE` | OCR recognition language | `ch` | No |
| `OCR_USE_GPU` | Use GPU acceleration | macOS=`false`, others=`true` | No |
| `OCR_PADDLE_DPI` | PaddleOCR rendering DPI (memory optimization) | `120` (aggressive optimization) / `150` (quality priority) | No |
| `OCR_SKIP_TABLE` | Skip table recognition (saves memory) | `false` | No |
| `OCR_SKIP_FORMULA` | Skip formula recognition (saves memory) | `false` | No |

### 2.6 OCR Timeout and Retry Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OCR_HEARTBEAT_TIMEOUT` | Heartbeat timeout (seconds), 0=disabled | `0` | No |
| `OCR_MAX_TOTAL_TIME` | Maximum total OCR execution time (seconds) | `252000` | No |
| `OCR_STALL_TIMEOUT` | OCR progress stall timeout (seconds) | `1800` | No |
| `OCR_MAX_RETRIES` | Maximum retries after subprocess crash | `2` | No |
| `OCR_RETRY_BACKOFF` | Retry interval (seconds), increases by 1.5x each time | `5.0` | No |
| `OCR_DYNAMIC_PARAMS` | Dynamically adjust OCR parameters based on system load | `true` | No |

### 2.7 Translation Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAX_WORKERS` | Maximum number of threads | `8` | No |
| `TRANSLATION_BATCH_SIZE` | Translation batch size | `10` | No |
| `USE_TWO_PHASE_MERGE` | Use two-phase parallel merge | `true` | No |
| `MERGE_MAX_WORKERS` | Maximum threads for parallel merge | `5` | No |
| `MERGE_BATCH_SIZE` | Number of text pairs per batch | `20` | No |

### 2.8 LLM OCR Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AIPING_OCR_LLM_MODEL` | aiping LLM OCR model | `DeepSeek-OCR` | No |
| `SILICON_FLOW_OCR_LLM_MODEL` | SiliconFlow LLM OCR model | `deepseek-ai/DeepSeek-OCR` | No |
| `QIANFAN_OCR_LLM_MODEL` | Qianfan LLM OCR model | None | No |
| `OCR_LLM_MAX_TOKENS` | LLM OCR maximum tokens | `8192` | No |
| `OCR_LLM_TEMPERATURE` | LLM OCR temperature | `0.1` | No |
| `OCR_LLM_DPI` | LLM OCR rendering DPI | `150` | No |

### 2.9 Per-Module API Parameter Configuration

Each translation service supports per-module overrides for translation, layout, glossary extraction model and temperature parameters:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TRANSLATION_TEMPERATURE` | Translation temperature parameter | `0.1` | No |
| `SEMANTIC_ANALYSIS_TEMPERATURE` | Semantic analysis temperature parameter | `0.1` | No |
| `GLOSSARY_TEMPERATURE` | Glossary extraction temperature parameter | `0.1` | No |
| `LAYOUT_TEMPERATURE` | Markdown layout temperature parameter | `0.1` | No |

These parameters are shared across all translators. CLI parameters (`--translation-model`, `--layout-model`, `--glossary-model`, `--ocr-llm-model`) can override the default model settings in `.env`.

### 2.10 Other Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEFAULT_DOC_TYPE` | Default document type | `AI技术` | No |

Supported document types: `AI技术`, `技术文档`, `商务文档`, `学术论文`, `法律文档`, `医学文档`

---

## 3. Running the Application

### 3.1 Web Service

```bash
python app.py
```

- **Default port**: 5000
- **Custom port**: `python app.py --port 8080`
- **Browser access**: `http://127.0.0.1:5000`
- **Upload limit**: 500MB

### 3.2 CLI

```bash
# Basic translation
python cli.py translate document.pdf

# Specify language and translation service
python cli.py translate document.pdf -s en -t zh -T silicon_flow

# Specify page range and output format
python cli.py translate document.pdf --pages "1-10,15" -f docx

# Enable semantic merge and LLM merge
python cli.py translate document.pdf -m -l

# Enable OCR mode
python cli.py translate document.pdf --ocr --ocr-engine paddleocr
```

### 3.3 AI IDE Skill

`SKILL.md` is a skill description file for AI IDEs (such as Trae, Cursor, etc.) that defines the capabilities and invocation methods of the pdftrans tool.

- **Purpose**: Enables AI IDEs to understand pdftrans functionality and automatically select appropriate parameters based on user requirements
- **Default behavior**: When no output format is specified, defaults to Markdown (split by chapter), with semantic merge and LLM merge enabled by default
- **Invocation**: After reading SKILL.md, the AI IDE automatically converts user natural language requests into CLI commands

---

## 4. CLI Complete Command Reference

### 4.1 `pdftrans translate <input>` — Translate a PDF File

| Parameter | Short | Type | Description | Default | Required |
|-----------|-------|------|-------------|---------|----------|
| `input` | — | positional | Input PDF file path | — | **Yes** |
| `--output` | `-o` | str | Output file path | Auto-generated | No |
| `--source` | `-s` | str | Source language code | `en` | No |
| `--target` | `-t` | str | Target language code | `zh` | No |
| `--translator` | `-T` | str | Translation service type: `aiping`/`silicon_flow`/`qianfan` | `aiping` | No |
| `--translation-model` | — | str | Override translation model (takes precedence over config file default) | None | No |
| `--layout-model` | — | str | Override Markdown layout model | None | No |
| `--glossary-model` | — | str | Override glossary extraction model | None | No |
| `--ocr-llm-model` | — | str | Override LLM OCR model | None | No |
| `--pages` | `-p` | str | Page range, e.g. `"1-5,7,9-10"` | All pages | No |
| `--format` | `-f` | str | Output format: `pdf`/`docx`/`markdown`/`pdf_docx`/`all` | `pdf` | No |
| `--glossary` | `-g` | str | Glossary file path | None | No |
| `--doc-type` | `-d` | str | Document type or domain description | `AI技术` | No |
| `--semantic-merge` | `-m` | flag | Enable semantic merge | `False` | No |
| `--llm-merge` | `-l` | flag | Use LLM semantic judgment | `False` | No |
| `--chapter-split` | `-c` | flag | Split output Markdown by chapter (only effective for Markdown format) | `False` | No |
| `--ocr` | — | flag | Enable OCR mode for scanned PDFs | `False` | No |
| `--ocr-engine` | — | str | OCR engine: `paddleocr`/`llm` | `paddleocr` | No |
| `--ocr-lang` | — | str | OCR recognition language | Auto-selected based on source language | No |

**Output format notes**:
- `pdf` → Generates a bilingual side-by-side PDF
- `docx` → Generates a Word document
- `markdown` → Generates Markdown files (packaged as `.zip`)
- `pdf_docx` → Generates both PDF and Word documents
- `all` → Generates PDF, Word, and Markdown

**Smart suffix handling**: The tool automatically adds the correct file suffix (`.pdf`, `.docx`, `.zip`) based on the output format.

### 4.2 `pdftrans glossary <input>` — Extract Glossary

| Parameter | Short | Type | Description | Default | Required |
|-----------|-------|------|-------------|---------|----------|
| `input` | — | positional | Input PDF file path | — | **Yes** |
| `--output` | `-o` | str | Output file path | Auto-generated `glossary_<name>.txt` | No |
| `--source` | `-s` | str | Source language code | `en` | No |
| `--target` | `-t` | str | Target language code | `zh` | No |
| `--translator` | `-T` | str | Translation service type | `aiping` | No |
| `--pages` | `-p` | str | Page range | All pages | No |
| `--doc-type` | `-d` | str | Document type or domain description | `AI技术` | No |

### 4.3 `pdftrans list-languages` — List Supported Languages

No additional parameters. Displays all supported language codes and names.

### 4.4 Global Options

| Parameter | Short | Description |
|-----------|-------|-------------|
| `--verbose` | `-v` | Show verbose output |
| `--version` | — | Show version number (1.0.0) |

---

## 5. Web API Reference

### 5.1 GET /

Home page route, renders the translation interface.

**Response**: HTML page with the following template variables:
- `supported_languages` — List of supported languages
- `default_source` — Default source language
- `default_target` — Default target language
- `default_translator` — Default translation service
- `default_doc_type` — Default document type

### 5.2 POST /translate

Submit a translation task (asynchronous).

**Request parameters** (`multipart/form-data`):

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `pdf_file` | file | PDF file (required) | — |
| `source_lang` | str | Source language code | `en` |
| `target_lang` | str | Target language code | `zh` |
| `translator` | str | Translation service: `aiping`/`silicon_flow`/`qianfan` | `silicon_flow` |
| `doc_type` | str | Document type | `AI技术` |
| `glossary` | str | Glossary content | Empty |
| `page_range` | str | Page range | Empty |
| `output_format` | str | Output format | `pdf` |
| `semantic_merge` | str | Enable semantic merge (`"on"` to enable) | Empty |
| `use_llm_merging` | str | Use LLM merge (`"on"` to enable) | Empty |
| `chapter_split` | str | Split by chapter (`"on"` to enable) | Empty |
| `ocr_mode` | str | Enable OCR (`"on"` to enable) | Empty |
| `ocr_engine` | str | OCR engine | `paddleocr` |

**Response**:

```json
{
  "success": true,
  "task_id": "uuid-string",
  "message": "Translation task started"
}
```

### 5.3 GET /progress/\<task_id\>

Poll translation task progress.

**Response**:

```json
{
  "success": true,
  "task_id": "uuid-string",
  "status": "processing",
  "progress": 65,
  "message": "Translating...",
  "result_file": "translated_xxx.pdf",
  "attachments": [],
  "error": null,
  "canceled": false,
  "warnings": [],
  "total_time": 120
}
```

### 5.4 POST /cancel/\<task_id\>

Cancel a translation task.

**Response**:

```json
{
  "success": true,
  "message": "Translation task canceled"
}
```

### 5.5 GET /download/\<filename\>

Download page route, renders the download interface.

**Parameter**: `filename` — File name (only alphanumeric characters, underscores, hyphens, and dots allowed)

### 5.6 GET /download_file/\<filename\>

Actual file download route.

**Parameter**: `filename` — File name (only alphanumeric characters, underscores, hyphens, and dots allowed)

**Response**: Sends the file attachment from the `OUTPUT_FOLDER` directory.

### 5.7 POST /get_pdf_pages

Get the total page count of a PDF file.

**Request parameters** (`multipart/form-data`):

| Parameter | Type | Description |
|-----------|------|-------------|
| `pdf_file` | file | PDF file (required) |

**Response**:

```json
{
  "success": true,
  "total_pages": 42
}
```

### 5.8 POST /extract_glossary

Extract glossary (asynchronous).

**Request parameters** (`multipart/form-data`):

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `pdf_file` | file | PDF file (required) | — |
| `source_lang` | str | Source language code | `en` |
| `target_lang` | str | Target language code | `zh` |
| `translator` | str | Translation service | `aiping` |
| `page_range` | str | Page range (max 1000 characters) | Empty |
| `doc_type` | str | Document type | `AI技术` |

**Response**:

```json
{
  "success": true,
  "task_id": "uuid-string",
  "message": "Glossary extraction task started"
}
```

### 5.9 GET /glossary_progress/\<task_id\>

Get glossary extraction task progress.

**Response**:

```json
{
  "success": true,
  "task_id": "uuid-string",
  "status": "processing",
  "progress": 50,
  "message": "Extracting glossary...",
  "glossary": "",
  "error": null
}
```

### 5.10 POST /glossary_cancel/\<task_id\>

Cancel a glossary extraction task.

**Response**:

```json
{
  "success": true,
  "message": "Glossary extraction task canceled"
}
```

---

## 6. Testing

### 6.1 Running Tests

```bash
# Run all tests (excluding slow tests)
pytest

# Run unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run end-to-end tests
pytest -m e2e

# Run slow tests
pytest -m slow

# Run a specific test file
pytest tests/test_translator.py

# Run a specific test class/method
pytest tests/test_translator.py::TestTranslator::test_translate

# Show verbose output
pytest -v

# Show print output
pytest -s
```

### 6.2 pytest Configuration

Configuration in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests, no external service dependencies
    integration: Integration tests, depend on external services
    e2e: End-to-end tests, depend on the complete system
    slow: Slow tests, containing time.sleep or long-running operations
addopts = --ignore=tests/test_simple_pdf_gen.py -m "not slow"
```

### 6.3 Test Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── data/                    # Test data
│   └── test_data_en_text.pdf
├── test_app.py              # Web application tests
├── test_cli.py              # CLI command tests
├── test_translator.py       # Translator base class tests
├── test_aiping_translator.py    # aiping translator tests
├── test_silicon_flow_translator.py  # SiliconFlow translator tests
├── test_translation_service.py    # Translation service tests
├── test_pdf_extractor.py    # PDF extractor tests
├── test_pdf_generator.py    # PDF generator tests
├── test_pdf_page_translation.py   # PDF page translation tests
├── test_ocr_extractor.py    # OCR extractor tests
├── test_ocr_worker.py       # OCR Worker tests
├── test_llm_ocr.py          # LLM OCR tests
├── test_llm_extractor_*.py  # LLM extractor series tests
├── test_markdown_generator.py     # Markdown generator tests
├── test_markdown_table.py   # Markdown table tests
├── test_markdown_chart_position.py  # Markdown chart position tests
├── test_markdown_download.py     # Markdown download tests
├── test_docx_generator.py   # Word document generator tests
├── test_semantic_merge.py   # Semantic merge tests
├── test_semantic_merge_extended.py  # Semantic merge extended tests
├── test_semantic_merge_optimization.py  # Semantic merge optimization tests
├── test_semantic_analyzer.py     # Semantic analyzer tests
├── test_batch_semantic_analysis.py   # Batch semantic analysis tests
├── test_glossary_extractor.py    # Glossary extractor tests
├── test_glossary_extraction.py   # Glossary extraction tests
├── test_glossary_file_operations.py  # Glossary file operation tests
├── test_chapter_*.py        # Chapter-related tests
├── test_table_*.py          # Table-related tests
├── test_text_splitting.py   # Text splitting tests
├── test_text_analyzer.py    # Text analyzer tests
├── test_progress.py         # Progress management tests
├── test_thread_safety.py    # Thread safety tests
└── ...
```

### 6.4 Shared Fixtures (conftest.py)

| Fixture Name | Description |
|--------------|-------------|
| `test_pdf_path` | Test PDF file path (`tests/data/test_data_en_text.pdf`) |
| `invalid_pdf_path` | Non-existent PDF file path |
| `mock_translator_response` | Mocked translation API response |
| `sample_text` | Sample English text |
| `source_lang` | Source language code (`"en"`) |
| `target_lang` | Target language code (`"zh"`) |
| `sample_translated_text` | Sample translated text |

---

## 7. Common Development Task Guide

### 7.1 Adding a New Translation API

Example: Adding a translation service named `new_provider`:

**Step 1: Create a translator subclass**

Create `new_provider_translator.py` under `modules/`:

```python
from modules.translator import Translator
from models.result_types import TranslationResult, TruncationInfo

class NewProviderTranslator(Translator):
    """NewProvider translator"""

    def __init__(self, api_key, api_url=None, model=None):
        super().__init__(api_key, api_url)
        self.model = model or 'default-model'

    def translate(self, text, source_lang, target_lang, doc_type, glossary):
        # Check if source and target languages are the same
        result = super().translate(text, source_lang, target_lang, doc_type, glossary)
        if result is not None:
            return result

        # Implement specific translation logic
        # 1. Generate system prompt (can reuse base class _generate_system_prompt)
        # 2. Call API
        # 3. Return TranslationResult object
        ...
```

**Step 2: Register with TranslationService**

Add to the `get_translator()` method in `services/translation_service.py`:

```python
elif translator_type == 'new_provider':
    if not config.NEW_PROVIDER_API_KEY:
        raise ValueError("NewProvider translation API configuration is incomplete")
    return NewProviderTranslator(
        config.NEW_PROVIDER_API_KEY,
        config.NEW_PROVIDER_API_URL,
        config.NEW_PROVIDER_MODEL
    )
```

**Step 3: Add configuration**

Add to `config.py`:

```python
NEW_PROVIDER_API_KEY = os.environ.get('NEW_PROVIDER_API_KEY')
NEW_PROVIDER_API_URL = os.environ.get('NEW_PROVIDER_API_URL') or 'https://api.newprovider.com/v1'
NEW_PROVIDER_MODEL = os.environ.get('NEW_PROVIDER_MODEL') or 'default-model'
```

Add corresponding variables to `.env.example`.

**Step 4: Update CLI options**

Update the `choices` for `--translator` in the translate subcommand in `cli.py`:

```python
choices=['aiping', 'silicon_flow', 'new_provider']
```

### 7.2 Adding a New OCR Engine

**Step 1: Create an OCR extractor subclass**

Create `new_engine_extractor.py` under `modules/ocr/`:

```python
from modules.ocr.base import OcrExtractor

class NewEngineOcrExtractor(OcrExtractor):
    """New OCR engine extractor"""

    def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None):
        # Implement specific OCR extraction logic
        # Return PdfExtraction object (same structure as PdfExtractor.extract())
        ...
```

**Step 2: Register with the factory function**

Add to `modules/ocr/factory.py`:

```python
SUPPORTED_OCR_ENGINES = ['paddleocr', 'llm', 'new_engine']

def create_ocr_extractor(ocr_type='paddleocr', **kwargs):
    if ocr_type == 'paddleocr':
        ...
    elif ocr_type == 'llm':
        ...
    elif ocr_type == 'new_engine':
        from modules.ocr.new_engine_extractor import NewEngineOcrExtractor
        return NewEngineOcrExtractor(**kwargs)
    else:
        raise ValueError(...)
```

**Step 3: Add configuration and CLI options**

Add corresponding configuration in `config.py` and `cli.py`.

### 7.3 Adding a New Output Format

**Step 1: Create a generator class**

Create a new generator under `modules/`, e.g. `html_generator.py`.

**Step 2: Integrate into TranslationService**

Add a new format generation logic branch in `services/translation_service.py`.

**Step 3: Add format option**

Add the new format to the `choices` of the `--format` parameter in `cli.py`, and add the corresponding option in the web frontend.

### 7.4 Modifying Translation Prompts

Translation prompts are defined in the `_generate_system_prompt()` method of `modules/translator.py`, organized into 4 sections:

| Section | Rules | Summary |
|---------|-------|---------|
| I. Core Principles | 1-4 | Semantic coherence, natural transitions, consistent style, concise and refined |
| II. Semantics & Style | 5-8 | Terminology consistency, no addition or omission, grammatical correctness, technical precision |
| III. Preserve Formatting | 9-13 | Do not translate URLs, preserve code blocks, length control, do not translate formulas, do not expand abbreviations |
| IV. No Meta-Commentary | 14-16 | No meta-commentary or original text output, preserve list formatting, preserve cell separator `|||` |

Language-specific rules are managed via `prompts/rule_registry.py`. The `rule_registry.merge_into_prompt()` function injects language-specific rules into the base prompt based on the source-target language pair, allowing per-language customization without modifying core rules.

**Modification notes**:
- After modifying prompts, always run translation tests to verify results
- Rules have interdependent constraints; modifying one may affect the effectiveness of others
- It is recommended to add language-specific rules via `prompts/language_rules/` rather than directly modifying core rules
- Fine-tune via the `--glossary` parameter and `doc_type` parameter for domain-specific adjustments

### 7.5 Adding a New Language

**Step 1: Update `SUPPORTED_LANGUAGES` in `config.py`**

```python
SUPPORTED_LANGUAGES = {
    'zh': '中文',
    'en': '英语',
    'ja': '日语',
    'ko': '韩语',
    'fr': '法语',
    'de': '德语',
    'es': '西班牙语',
    'ru': '俄语',
    'pt': '葡萄牙语',  # New addition
}
```

**Step 2: Update CLI options**

Add the new language code to the `choices` of `--source` and `--target` parameters in `cli.py`.

**Step 3: Update translator base class**

Add the new language to the `supported_languages` dictionary in `modules/translator.py`.

**Step 4: Update OCR language mapping**

If using OCR mode, add the corresponding recognition language code for the new language in the OCR engine.

**Step 5: Add language-specific rules (optional)**

If the new language requires special translation rules, create a rule module under `prompts/language_rules/`:

1. Create a file named `<source>_to_<target>.py` (e.g., `bo_to_zh.py` for Tibetan-to-Chinese)
2. Define a `get_rules()` function that returns a list of rule strings specific to this language pair
3. Register the rule module in `prompts/rule_registry.py`

The `rule_registry.merge_into_prompt()` function will automatically inject these rules into the base prompt when the corresponding language pair is used.

---

## 8. Code Conventions and Practices

### 8.1 Factory Pattern

The factory pattern is widely used throughout the project to create different types of instances:

| Factory | File | Supported Types |
|---------|------|----------------|
| OCR extractor factory | `modules/ocr/factory.py` | `paddleocr`, `llm` |
| Markdown generator factory | `modules/markdown_generator.py` (`create_markdown_generator()`) | `aiping`, `silicon_flow` |
| Semantic analyzer factory | `modules/semantic_analyzer_factory.py` | `aiping`, `silicon_flow` |
| Translator factory | `services/translation_service.py` (`get_translator()`) | `aiping`, `silicon_flow`, `qianfan` |

### 8.2 Strategy Pattern

Translators and OCR engines use the strategy pattern, achieving interchangeability through unified base class interfaces:

- **Translators**: `Translator` base class → `AipingTranslator`, `SiliconFlowTranslator`, `QianfanTranslator`
- **OCR engines**: `OcrExtractor` base class → `PaddleOcrExtractor`, `LlmOcrExtractor`

### 8.3 Subprocess Isolation

PaddleOCR runs in an isolated subprocess (`modules/ocr/ocr_worker.py`) to prevent GIL and memory leaks from affecting the main process. Key mechanisms:

- Subprocess communicates results via queues
- Supports heartbeat detection and timeout handling
- Automatic retry after subprocess crash (up to `OCR_MAX_RETRIES` times)

### 8.4 Parallel Processing

Parallel processing is implemented using `ThreadPoolExecutor`:

- **Translation**: Multi-threaded parallel translation of text chunks
- **Glossary extraction**: Multi-threaded parallel term extraction
- **Markdown chapter generation**: Multi-threaded parallel generation of chapter files

Thread count is controlled by `MAX_WORKERS` (default 8).

### 8.5 Graceful Degradation

| Scenario | Degradation Strategy |
|----------|---------------------|
| Translation failure | Fall back to original text |
| Formula rendering failure | Degrade to plain text display |
| Text overflow | Automatically reduce font size or truncate |
| OCR subprocess crash | Automatic retry (up to 2 times) |
| Markdown layout model failure | Raise exception (no degradation) |

### 8.6 Progress Management

Fine-grained progress tracking based on `PHASE_CONFIG`, defined in `models/phase_config.py`:

**Translation task phases**:

| Phase ID | Name | Progress Range |
|----------|------|---------------|
| `init` | Initialization | 0% - 5% |
| `extraction` | Text and chart extraction | 5% - 40% |
| `semantic_merge` | Semantic merge | 40% - 50% |
| `translation` | Text translation | 50% - 85% |
| `table_translation` | Table translation | 85% - 92% |
| `generation` | Output generation | 92% - 98% |
| `clean` | Cleanup temporary files | 98% - 100% |

**Glossary extraction phases**:

| Phase ID | Name | Progress Range |
|----------|------|---------------|
| `init` | Start extraction | 0% - 5% |
| `pdf_extraction` | Text extraction | 5% - 30% |
| `term_extraction` | Term extraction | 30% - 100% |

### 8.7 Task Cancellation

Task cancellation is implemented via the `Task.canceled` flag:

- Web: `POST /cancel/<task_id>` sets `canceled=True`
- CLI: `KeyboardInterrupt` triggers cancellation
- Each processing phase periodically checks the `canceled` flag and exits promptly

### 8.8 Logging Conventions

```python
from utils.logging_config import get_logger

logger = get_logger(__name__)
```

- Use `get_logger(__name__)` to obtain a module-level logger
- Do not use `print()` for debug output
- In web mode, werkzeug HTTP log level is set to ERROR

### 8.9 Error Classification

The OCR module defines two error types:

- **`OcrRetryableError`**: Retryable errors (e.g., subprocess crash, timeout), automatically retried
- **`OcrFatalError`**: Fatal errors (e.g., file not found, invalid parameters), fails immediately

---

## 9. Supported Languages

| Language Code | Language Name |
|--------------|---------------|
| `zh` | Chinese |
| `en` | English |
| `ja` | Japanese |
| `ko` | Korean |
| `fr` | French |
| `de` | German |
| `es` | Spanish |
| `ru` | Russian |
| `bo` | Tibetan |

Default source language: `en` (English)
Default target language: `zh` (Chinese)
