# PDF Translation Tool

## Project Overview

PDF Translation Tool is a PDF document translation tool that supports multiple translation APIs. It can accurately extract PDF content, translate using various translation services, and generate well-formatted translated PDF/Word documents.

If you have any questions or suggestions during use, welcome to leave a message on the WeChat public account 【智践行】, or submit Issues or Pull Requests on the Gitee repository. We look forward to working with everyone to refine the PDF translation tool to better meet practical needs!

## Features

### Core Features

- **PDF Text Extraction**: Supports extracting plain text and table content while preserving position information
- **Multiple Translation API Support**:
  - aiping Model API
  - Silicon Flow Model API
- **Document Generation**:
  - PDF Generation: Generates translated PDF based on the original PDF, preserving original layout and formatting
  - Word Generation: Generates Word documents based on merged translation results, preserving original fonts and styles
  - Markdown Generation: Generates Markdown documents based on layout model, supporting correct table and image positioning
- **Web Interface**: Provides a clean and easy-to-use web interface for file upload, translation service selection, and result download
- **Page-specific Translation**: Supports translating specific page numbers or page ranges to improve translation efficiency
- **Output Format Selection**: Supports selecting output as PDF, Word, Markdown, or any combination
- **Automatic Glossary Extraction**: Automatically extracts glossaries from uploaded PDFs, supporting both aiping and Silicon Flow platforms

### Technical Features

- **Virtual Environment Management**: Supports conda virtual environments
- **Modular Design**: Clear code structure for easy maintenance and extension
- **API Key Security**: Uses environment variables to manage API keys, avoiding hardcoding
- **Error Handling**: Friendly error prompts and handling mechanisms

## Tech Stack

- **Programming Language**: Python 3.9+
- **Virtual Environment**: conda
- **Web Framework**: Flask 3.0+
- **PDF Processing**:
  - PyMuPDF (fitz) 1.23+: Used for PDF text extraction and generation
  - camelot-py\[cv]: Used for table extraction
  - opencv-python: Dependency for camelot-py\[cv]
- **Document Processing**:
  - python-docx: Used for Word document generation
- **Translation APIs**: aiping Translation API, Silicon Flow Translation API
- **API Client**: openai: Used for calling translation APIs
- **Testing Framework**: pytest
- **Version Control**: Git + Gitee

## Installation

### 1. Clone Repository

```bash
git clone https://gitee.com/chunju/pdfTrans.git
cd pdfTrans
```

### 2. Create and Activate Conda Environment

```bash
conda env create -f environment.yml
conda activate pdfTrans
```

### 3. Configure Environment Variables

- Copy `.env.example` file to `.env`
- Configure API keys for translation or model calling in the `.env` file

```bash
cp .env.example .env
# Edit .env file to add API keys
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Start Web Service

```bash
python app.py
```

### Access Web Interface

- Open browser and visit `http://localhost:5000`
- Upload PDF file
- System automatically detects and displays total PDF pages
- Select translation page range (optional, default selects all pages)
  - Supports single page numbers (e.g., 1,3,5)
  - Supports page ranges (e.g., 1-5,7-10)
  - Can mix both (e.g., 1-3,5,7-9)
- Select translation service and target language
- Select output format (PDF, Word, Markdown, or any combination)
- Click "Translate" button
- Wait for translation to complete, download translated PDF and/or Word files

### Command Line Usage

The tool now supports command line interface (CLI) for batch processing and automation workflows.

#### Installation

```bash
# Install the CLI tool
pip install -e .

# Or use directly without installation
python cli.py --help
```

#### Basic Commands

```bash
# Translate a PDF file
pdftrans translate document.pdf -o translated.pdf

# Specify source and target languages
pdftrans translate document.pdf -s en -t zh -o output.pdf

# Use specific translation service
pdftrans translate document.pdf -T silicon_flow -o output.pdf

# Translate specific pages
pdftrans translate document.pdf --pages "1-10,15,20-25" -o output.pdf

# Generate Word document
pdftrans translate document.pdf -f docx -o output.docx

# Generate Markdown with chapter split
pdftrans translate document.pdf -f markdown --chapter-split -o output/

# Use glossary file
pdftrans translate document.pdf -g glossary.txt -o output.pdf

# Enable semantic merge
pdftrans translate document.pdf --semantic-merge -o output.pdf

# Extract glossary
pdftrans glossary document.pdf -o glossary.txt

# List supported languages
pdftrans list-languages
```

#### Output Directory and Temporary Files

- **Output Directory**: When using the `-o` parameter, the tool will generate output files directly in the specified directory. If no output directory is specified, the default `outputs/` directory will be used.

- **Temporary Files**: The tool automatically creates a temporary subdirectory in the output directory to store intermediate files such as extracted images and Markdown files. This ensures that image extraction works correctly even in sandbox mode with restricted permissions.

- **Markdown Processing**: For Markdown output, the tool first generates Markdown files in the temporary directory and then packages them into a zip file if chapter split is enabled.

#### CLI Options

**Global Options:**
- `-v, --verbose` - Show detailed output
- `--version` - Show version information
- `-h, --help` - Show help message

**Translate Command Options:**
- `-o, --output` - Output file path (auto-generated if not specified)
- `-s, --source` - Source language code (default: en)
- `-t, --target` - Target language code (default: zh)
- `-T, --translator` - Translation service (aiping/silicon_flow, default: aiping)
- `-p, --pages` - Page range (e.g., "1-5,7,9-10")
- `-f, --format` - Output format (pdf/docx/markdown, default: pdf)
- `-g, --glossary` - Glossary file path
- `-d, --doc-type` - Document type or domain description (default: AI技术)
- `-m, --semantic-merge` - Enable semantic merge
- `-l, --llm-merge` - Use LLM for merging
- `-c, --chapter-split` - Split output by chapter (Markdown only)

**Glossary Command Options:**
- `-o, --output` - Output file path
- `-s, --source` - Source language code
- `-t, --target` - Target language code
- `-T, --translator` - Translation service
- `-p, --pages` - Page range
- `-d, --doc-type` - Document type

#### Supported Languages

- `zh` - Chinese
- `en` - English
- `ja` - Japanese
- `ko` - Korean
- `fr` - French
- `de` - German
- `es` - Spanish
- `ru` - Russian

## Project Structure

```
pdfTrans/
├── .trae/
│   ├── documents/           # Documentation directory
│   │   └── ai_dev_progress.md # AI development progress record file
│   ├── rules/
│   │   └── project_rules.md # Project rules file
│   └── tmp/                 # Code/data analysis scripts and related data generated during AI-assisted development
├── .git/                    # Git repository directory
├── .gitignore               # Git ignore file
├── app.py                   # Flask application entry, only contains Flask app initialization and routing
├── requirements.txt         # Dependencies list
├── environment.yml          # Conda environment configuration
├── config.py                # Configuration file
├── .env.example            # Environment variables example file
├── README.md               # Project documentation
├── pytest.ini              # Pytest configuration file
├── docs/                   # Project documentation directory
├── models/                 # Data models
│   ├── task.py             # Task data model
│   ├── text_block.py       # Text block model
│   ├── merged_block.py     # Merged block model
│   └── extraction.py       # Extraction model
├── services/               # Business logic services
│   ├── task_service.py     # Task management service
│   └── translation_service.py # Translation business service
├── utils/                  # Utility tools
│   ├── text_processing.py  # Text processing utilities
│   ├── logging_config.py   # Logging configuration
│   └── file_utils.py       # File processing utilities
├── modules/                # Core functional modules
│   ├── extractors/         # Extractor modules
│   │   ├── __init__.py
│   │   ├── coordinate_utils.py
│   │   ├── page_utils.py
│   │   ├── style_analyzer.py
│   │   ├── table_processor.py
│   │   └── text_analyzer.py
│   ├── pdf_extractor.py    # PDF extraction module
│   ├── pdf_generator.py    # PDF generation module
│   ├── docx_generator.py   # Word generation module
│   ├── markdown_generator.py # Markdown generation module
│   ├── translator.py       # Translation base class
│   ├── aiping_translator.py # aiping translation module
│   └── silicon_flow_translator.py # Silicon Flow translation module
├── prompt/                 # Prompt directory
├── temp_images/            # Temporary images directory
├── tests/                  # Test scripts directory
│   ├── test_*.py           # Test scripts
├── static/                 # Static resources
│   ├── css/                # CSS style files
│   │   └── style.css
│   └── js/                # JavaScript files
│       └── main.js
├── templates/              # Template files
│   ├── index.html          # Main page template
│   └── download.html       # Download page template
├── uploads/                # Uploaded files directory
└── outputs/                # Output files directory
```

## Development Workflow

### Branch Management

- **main**: Main branch, only for releasing stable versions
- **develop**: Development branch, integrates feature branches
- **feature/xxx**: Feature branch, for developing new features
- **bugfix/xxx**: Bug fix branch
- **release/xxx**: Release branch, for preparing releases

### Commit Message Format

- Format: `[Type] Short description`
- Types include: feat (new feature), fix (bug fix), docs (documentation), style (code style), refactor (refactoring), test (testing), chore (build/tools)
- Example: `feat: Add Baidu translation API wrapper`

### Testing Standards

- All test scripts must be placed in `tests/` directory with naming format `test_*.py`
- Use pytest framework for testing
- Unit test coverage should be at least 80%

### Running Tests

#### Install Dependencies

pytest is included in requirements.txt, just run the dependency installation command:

```bash
pip install -r requirements.txt
```

#### Test Commands

- Run all tests:
  ```bash
  pytest
  ```
- Run specific module tests:
  ```bash
  pytest tests/test_pdf_extractor.py
  ```
- Run tests and generate coverage report:
  ```bash
  pytest --cov=modules/ tests/
  ```

#### Test File List

- `test_pdf_extractor.py`: PDF extraction module tests
- `test_translator.py`: Translation base class tests
- `test_aiping_translator.py`: aiping translation tests
- `test_silicon_flow_translator.py`: Silicon Flow translation tests
- `test_pdf_generator.py`: PDF generation module tests
- `test_markdown_download.py`: Markdown download tests
- `test_markdown_chart_position.py`: Markdown chart position tests
- `test_markdown_table.py`: Markdown table tests
- `conftest.py`: Test configuration file

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/xxx`
3. Commit code: `git commit -m "feat: Add xxx feature"`
4. Push branch: `git push origin feature/xxx`
5. Submit Pull Request

## License

MIT License

## Contact

If you have any questions or suggestions during use, welcome to leave a message on the WeChat public account 【智践行】, or submit Issues or Pull Requests on the Gitee repository. We look forward to working with everyone to refine the PDF translation tool to better meet practical needs!

## Changelog

The project changelog has been moved to a separate [docs/CHANGELOG.md](docs/CHANGELOG.md) file.

## Task List

The project task list is available in [docs/TODO.md](docs/TODO.md).

## Notes

1. This tool only supports non-scanned PDFs, OCR is not supported
2. Translation quality depends on the selected translation API
3. Processing large PDF documents may take a long time, you can use the page-specific translation feature to translate in batches
4. Please ensure API keys are correctly configured, otherwise translation functionality will not work
