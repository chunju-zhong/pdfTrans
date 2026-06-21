# PDF Translation Tool

## Project Overview

PDF Translation Tool is a PDF document translation tool that supports multiple translation APIs. It can be called through Web service/CLI command line/SKILL methods, accurately extract PDF content, translate using multiple translation services, and generate well-formatted translated PDF/Word documents.

If you have any questions or suggestions during use, welcome to leave a message on the WeChat public account 【智践行】or RED 【智践行的小芝】, or submit Issues or Pull Requests on the Gitee repository. We look forward to working with everyone to refine the PDF translation tool to better meet practical needs!

## Features

### Core Features

- **PDF Text Extraction**: Supports extracting plain text and table content while preserving position information
- **OCR Support**: Supports two OCR engines
  - **PaddleOCR** (local engine): Based on PP-StructureV3, supports layout analysis, text recognition, formula recognition and table extraction. Requires PaddlePaddle installation.
  - **LLM OCR** (cloud engine): Based on DeepSeek-OCR and other vision LLMs, called via translation service API. No PaddlePaddle installation needed. Ideal for machines without GPU or when better layout understanding is required.
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
- **OCR Engine**:
  - PaddleOCR 3.0+ (PP-StructureV3): Used for PDF text extraction, layout analysis, formula recognition
  - PaddlePaddle 3.0+: Deep learning framework (CPU/GPU auto-detection)
- **Document Processing**:
  - python-docx: Used for Word document generation
- **Translation APIs**: aiping Translation API, Silicon Flow Translation API
- **API Client**: openai: Used for calling translation APIs
- **Testing Framework**: pytest
- **Version Control**: Git + Gitee

## Installation

### 1. Clone Repository

Gitee: https://gitee.com/chunju/pdfTrans
GitHub: https://github.com/chunju-zhong/pdfTrans

```bash
git clone https://gitee.com/chunju/pdfTrans.git
# or
git clone https://github.com/chunju-zhong/pdfTrans.git

cd pdfTrans
```

### 2. Create and Activate Conda Environment

```bash
conda env create -f environment.yml
conda activate pdfTrans
```

### 3. Configure Environment Variables

- Copy `.env.example` file to `.env`
- Register for an Aiping account: https://aiping.cn
- Or, register for a Silicon Flow account: https://cloud.siliconflow.cn/i/OFUfQfNj
- Obtain your API key
- Configure platform model names and API keys in the `.env` file

```bash
cp .env.example .env
```

- Edit `.env` file to add API keys and configure model names

```bash
# aiping API configuration
AIPING_API_KEY=your-secret-key
AIPING_API_URL=https://aiping.cn/api/v1
# Specify translation model
AIPING_MODEL_TRANSLATION=Qwen3-32B
# Specify Markdown layout model
AIPING_MODEL_LAYOUT=Qwen3-32B
# Specify glossary extraction model
AIPING_MODEL_GLOSSARY=Qwen3-32B

# Silicon Flow API configuration
SILICON_FLOW_API_KEY=your-secret-key
SILICON_FLOW_API_URL=https://api.siliconflow.cn/v1/
# Specify translation model
SILICON_FLOW_MODEL_TRANSLATION=tencent/Hunyuan-MT-7B
# Specify Markdown layout model
SILICON_FLOW_MODEL_LAYOUT=Qwen/Qwen3-32B
# Specify glossary extraction model
SILICON_FLOW_MODEL_GLOSSARY=Qwen/Qwen3-32B

# LLM OCR configuration (reuses translation engine API Key, only need to specify model)
AIPING_OCR_LLM_MODEL=DeepSeek-OCR-2
SILICON_FLOW_OCR_LLM_MODEL=deepseek-ai/DeepSeek-OCR
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Install PaddlePaddle (OCR Support)

PaddlePaddle CPU and GPU versions are mutually exclusive and cannot be installed simultaneously. Use the auto-detection script:

```bash
bash install_paddle.sh
```

Or install manually:

```bash
# CPU version (default, works on all platforms)
pip install paddlepaddle>=3.0.0

# GPU version (requires NVIDIA GPU + CUDA 11.8+)
pip install paddlepaddle-gpu>=3.0.0
```

> **Note**: OCR requires PaddlePaddle (for PaddleOCR engine) or LLM OCR model configuration (for LLM OCR engine). If neither is configured, only non-scanned PDFs can be processed.

### 6. Install LaTeX (Optional, for High-Quality Formula Rendering)

LaTeX is used for high-quality formula rendering (usetex mode). If not installed, the system will automatically fall back to matplotlib mathtext for formula rendering (functional but with reduced quality for complex formulas).

```bash
# macOS
brew install --cask mactex

# Or install minimal version (smaller footprint)
brew install --cask basictex

# Linux (Ubuntu/Debian)
sudo apt-get install texlive-full

# Or install minimal version (smaller footprint)
sudo apt-get install texlive-latex-base texlive-fonts-recommended
```

> **Note**: After installation, ensure `latex` command is available in your terminal.

## Usage

This tool provides two **independent** usage methods: **Web Interface** and **Command Line (CLI)**. No need to start the Web service to use CLI.

### Method 1: Web Interface (GUI)

#### Start Service

```bash
python app.py
```

#### Access Interface

- Open browser and visit `http://localhost:5000`
- Upload PDF file
- System automatically detects and displays total PDF pages
- Select translation page range (optional, default selects all pages)
  - Supports single page numbers (e.g., 1,3,5)
  - Supports page ranges (e.g., 1-5,7-10)
  - Can mix both (e.g., 1-3,5,7-9)
- Select translation service and target language
- Select output format (PDF, Word, Markdown, or any combination)
- Enable OCR mode (optional)
  - Check "Enable OCR" to use OCR engine for text extraction
  - Select OCR engine:
    - **PaddleOCR** (local engine): Requires PaddlePaddle, suitable for local environments with GPU
    - **LLM OCR** (cloud engine): Uses vision LLM via API, no PaddlePaddle needed, suitable for environments without GPU
  - System auto-detects GPU and uses GPU acceleration when available (PaddleOCR engine)
- Click "Translate" button
- Wait for translation to complete, download translated PDF and/or Word files

---

### Method 2: Command Line (CLI, Standalone, No Web Service Required)

CLI is ideal for batch processing and automation workflows. It runs **independently without the Web service**.

#### Installation

```bash
# Navigate to project directory first, then install CLI tool
cd pdfTrans  # Replace with your actual project path
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

# Enable OCR mode
pdftrans translate document.pdf --ocr -o output.pdf

# Specify OCR engine and language
pdftrans translate document.pdf --ocr --ocr-engine paddleocr --ocr-lang en -o output.pdf

# Use LLM OCR cloud engine (no PaddlePaddle required)
pdftrans translate document.pdf --ocr --ocr-engine llm -o output.pdf

# Use glossary during translation
pdftrans translate document.pdf -g glossary.txt -o output.pdf

# Extract glossary
pdftrans glossary document.pdf -o glossary.txt

# List supported languages
pdftrans list-languages
```

#### CLI Options Reference

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
- `--ocr` - Enable OCR mode
- `--ocr-engine` - OCR engine type: `paddleocr` (local, requires PaddlePaddle) or `llm` (cloud, requires API Key), default: paddleocr
- `--ocr-lang` - OCR recognition language (default: auto-detect from source language)

---

### Method 3: AI IDE Skill (Natural Language Invocation, No Manual Commands)

If you use an AI IDE that supports Skills (such as **Trae**), you can invoke the PDF translation tool through **natural language**. The AI will automatically assemble and execute CLI commands for you.

#### Installation & Setup (Using Trae as Example)

1. **Install Trae IDE**: Visit https://www.trae.com to download and install
2. **Install Skill**: Download this repository (pdfTrans) into your project's skill directory:
   ```
   your-project/
   └── .trae/
       └── skills/
           └── pdftrans/    ← Place pdfTrans code here
               ├── SKILL.md   ← Trae identifies and activates the skill via this file
               ├── cli.py
               └── ...
   ```
3. **Activate Skill**: Trae will automatically detect the `SKILL.md` file, and you can use the PDF translation skill directly in the chat window

> **Note**: The skill invokes CLI commands via `SKILL.md` to execute translation tasks. Just ensure API keys are configured in `.env` (see "**Step 3: Configure Environment Variables**" above).

#### How to Use

Simply describe your needs in natural language within the AI IDE's chat window, for example:

- "Translate this PDF to Chinese"
- "Translate this PDF to Chinese and output as a Word document"
- "Translate pages 1-10 using silicon_flow translation service"
- "Extract glossary from this PDF"
- "List languages supported by PDF translation tool"

#### Skill Enhanced Features

When invoked via Skill, the AI automatically provides these enhancements:

- **Smart Defaults**: Automatically detects source language from the first 100 lines of the input file, defaults to Chinese as target language
- **Optimized Output**: Defaults to Markdown format with chapter split, semantic merge, and LLM semantic judgment enabled
- **Error Handling**: Provides clear error messages for common issues like permission errors

> **Note**: The skill mode invokes CLI commands via `SKILL.md` to execute translations. Please ensure you have completed the **Installation Steps** above (conda environment, dependencies, API keys) and can successfully run `pdftrans --help`.

## License

AGPL-3.0

## Contact

If you have any questions or suggestions during use, welcome to leave a message on the WeChat public account 【智践行】or RED/Xiaohongshu 【智践行的小芝】, or submit Issues or Pull Requests on the Gitee repository. We look forward to working with everyone to refine the PDF translation tool to better meet practical needs!

## Changelog

The project changelog has been moved to a separate [docs/CHANGELOG.md](docs/CHANGELOG.md) file.

## Task List

The project task list is available in [docs/TODO.md](docs/TODO.md) file.

## Notes

1. OCR mode provides enhanced text extraction with layout analysis, formula and table recognition (requires PaddlePaddle or LLM OCR configuration)
2. Translation quality depends on the selected translation API
3. Processing large PDF documents may take a long time, you can use the page-specific translation feature to translate in batches
4. Please ensure API keys are correctly configured, otherwise translation functionality will not work