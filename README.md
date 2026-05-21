# PDF Translation Tool

## Project Overview

PDF Translation Tool is a PDF document translation tool that supports multiple translation APIs. It can be called through Web service/CLI command line/SKILL methods, accurately extract PDF content, translate using multiple translation services, and generate well-formatted translated PDF/Word documents.

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
  - camelot-py[cv]: Used for table extraction
  - opencv-python: Dependency for camelot-py[cv]
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
# Translate a PDF file, default uses aiping model service, translates English to Chinese, outputs as pdf, does not enable semantic merge and LLM semantic judgment
pdftrans translate document.pdf -o translated.pdf

# Specify source and target languages
pdftrans translate document.pdf -s en -t zh -o output.pdf

# Use specific translation service, such as silicon_flow
pdftrans translate document.pdf -T silicon_flow -o output.pdf

# Translate specific pages
pdftrans translate document.pdf --pages "1-10,15,20-25" -o output.pdf

# Generate Word document
pdftrans translate document.pdf -f docx -o output.docx

# Generate Markdown and split chapters
pdftrans translate document.pdf -f markdown --chapter-split -o output/

# Enable semantic merge
pdftrans translate document.pdf --semantic-merge -o output.pdf

# Enable semantic merge and LLM semantic judgment
pdftrans translate document.pdf -m -l -f docs -o output.pdf

# Use glossary during translation
pdftrans translate document.pdf -g glossary.txt -o output.pdf

# Extract glossary
pdftrans glossary document.pdf -o glossary.txt

# List supported languages
pdftrans list-languages
```

#### Skill Integration

PDF translation tool includes skill integration and provides enhanced features:

- **Smart Defaults**: Automatically detects source language from the first 100 lines of the input file, defaults to Chinese as target language
- **Optimized Output**: Defaults to Markdown format with chapter split, semantic merge, and LLM semantic judgment enabled
- **Error Handling**: Provides clear error messages for common issues like permission errors

#### Skill Usage

You can use **Natural Language Usage** (in AI IDEs like Trae): You can use natural language to interact with the skill, for example:
   - "Translate this PDF to Chinese"
   - "Translate this PDF to Chinese and output as Word document"
   - "Extract glossary from this PDF"
   - "List languages supported by PDF translation tool"

#### API Key Configuration

The tool requires API keys for translation services. Configure them in the `.env` file:

```bash
# .env file example

# aiping API configuration
AIPING_API_KEY=your_aiping_api_key

# Silicon Flow API configuration
SILICON_FLOW_API_KEY=your_silicon_flow_api_key
```

Only one translation service API key is required to use the tool. The tool defaults to using aiping model service.

#### CLI Options

**Global Options:**
- `-v, --verbose` - Show detailed output
- `--version` - Show version information
- `-h, --help` - Show help message
- `-o, --output` - Output file path
- `-s, --source` - Source language code
- `-t, --target` - Target language code
- `-T, --translator` - Translation service
- `-p, --pages` - Page range
- `-d, --doc-type` - Document type

**Translate Command Options:**
- `-o, --output` - Output file path (auto-generated if not specified)
- `-f, --format` - Output format (pdf/docx/markdown, default: pdf)
- `-g, --glossary` - Glossary file path
- `-m, --semantic-merge` - Enable semantic merge
- `-l, --llm-merge` - Use LLM semantic judgment
- `-c, --chapter-split` - Split output by chapter (Markdown only)

## License

AGPL-3.0

## Contact

If you have any questions or suggestions during use, welcome to leave a message on the WeChat public account 【智践行】, or submit Issues or Pull Requests on the Gitee repository. We look forward to working with everyone to refine the PDF translation tool to better meet practical needs!

## Changelog

The project changelog has been moved to a separate [docs/CHANGELOG.md](docs/CHANGELOG.md) file.

## Task List

The project task list is available in [docs/TODO.md](docs/TODO.md) file.

## Notes

1. This tool only supports non-scanned PDFs, OCR is not supported
2. Translation quality depends on the selected translation API
3. Processing large PDF documents may take a long time, you can use the page-specific translation feature to translate in batches
4. Please ensure API keys are correctly configured, otherwise translation functionality will not work