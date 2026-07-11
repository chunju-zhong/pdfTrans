# pdfTrans Technical Guide Document

This document details the core technical implementation of the pdfTrans project, covering the OCR pipeline, translation pipeline, semantic merging, multi-format generation, table processing, formula rendering, terminology extraction, error handling, and progress management subsystems.

---

## 1. OCR Pipeline Architecture

### 1.1 Dual-Engine Design

The project adopts a dual OCR engine architecture, created on demand via the factory pattern:

- **PaddleOCR Local Engine** (`PaddleOcrExtractor`): Based on PP-StructureV3, supports layout analysis, table recognition, and formula detection. Suited for high-performance local processing.
- **LLM Cloud Engine** (`LlmOcrExtractor`): Based on DeepSeek-OCR / VLM JSON, supports visual-understanding document parsing. Suited for complex layouts and scanned documents.

The factory function `create_ocr_extractor(ocr_type='paddleocr', **kwargs)` is defined in `modules/ocr/factory.py`, with `SUPPORTED_OCR_ENGINES = ['paddleocr', 'llm']`.

The abstract base class `OcrExtractor(ABC)` is defined in `modules/ocr/base.py`, with the core interface:

```python
@abstractmethod
def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None):
    pass
```

### 1.2 PaddleOCR Engine

#### 1.2.1 Stepwise Loading Strategy

`PaddleOcrExtractor` uses PP-StructureV3 stepwise loading to avoid loading all models at once:

- `STEP_LAYOUT_OCR = 1`: Layout analysis + text OCR
- `STEP_IMAGE_CROP = 2`: Image cropping

The `_create_pipeline()` method creates the PPStructure pipeline with unnecessary preprocessing disabled to improve performance:

```python
kwargs = dict(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    text_det_thresh=0.3,
    text_det_box_thresh=0.5,
    text_rec_score_thresh=0.5,
)
```

#### 1.2.2 Label Classification System

PP-StructureV3 output labels are divided into four groups:

| Label Set | Included Labels | Purpose |
|-----------|----------------|---------|
| `TEXT_LABELS` | text | Body text |
| `TITLE_LABELS` | title | Headings |
| `IMAGE_LABELS` | figure, figure_caption, table | Image and table regions |
| `NON_BODY_LABELS` | header, footer, reference, equation | Non-body regions |

#### 1.2.3 Supplementary Capture Mechanism

`_filter_uncovered_textlines()` detects text lines not covered by layout analysis, using a 5px expansion tolerance and 15px vertical grouping threshold to assign missed text lines to the nearest parent region.

#### 1.2.4 Table Grid Computation

`_compute_table_grid()` calculates grid layout based on tightly-bounded textline row/column bboxes:

1. Cluster textlines by y-coordinate into rows
2. Cluster by x-coordinate into columns
3. Cumulatively compute the grid layout
4. Detect cell alignment relationships
5. Calculate `estimated_lines` (estimated number of text lines per cell)

#### 1.2.5 HTML Table Parsing

The `_TableHtmlParser` class parses HTML-format tables output by PP-StructureV3. `_parse_html_table()` and `_expand_html_table()` handle merged cells (rowspan/colspan).

### 1.3 LLM OCR Engine

#### 1.3.1 Three-Stage Response Parsing

`LlmOcrExtractor._parse_response()` implements a three-stage parsing pipeline:

1. **Format Detection**: Automatically identifies the response format (`<|ref|>` tags / JSON / Markdown)
2. **Structured Parsing**: Invokes the corresponding parser based on format
   - `_parse_ref_tags_to_blocks()`: Parses DeepSeek-OCR's `<|ref|>` tag format
   - `_parse_json_to_blocks()`: Parses VLM JSON format
   - `_parse_markdown_to_blocks()`: Parses Markdown format
3. **Model Mapping**: `_map_ocr_blocks_to_models()` maps `OcrBlock` dataclasses to internal models

#### 1.3.1a Parser Split

LLM OCR response parsing has been split from `LlmOcrExtractor` into independent modules:

- `modules/ocr/llm_response_parser.py` (`LlmOcrResponseParser`): Handles format detection and structured parsing of text content (`<|ref|>` tags / JSON / Markdown)
- `modules/ocr/llm_table_parser.py` (`LlmTableParser`): Handles table layout computation, implementing the row-height-priority iterative optimization algorithm

After the split, `LlmOcrExtractor` is only responsible for API calls and page-level orchestration, delegating parsing logic to the two parsers above.

#### 1.3.1b Blank Page Detection

`LlmOcrExtractor` adds a `_is_blank_image()` method that detects whether a page is blank before calling the LLM API:

- Calculates the standard deviation of image pixels; when below a threshold, the page is determined to be blank
- Blank pages skip the LLM call, returning empty results, saving API call costs

#### 1.3.1c Timeout Handling

LLM OCR calls now catch `APITimeoutError`. On timeout, a warning is logged and the current page is skipped without interrupting the overall flow.

#### 1.3.2 DeepSeek-OCR Normalized Coordinates

DeepSeek-OCR uses a 0-999 normalized coordinate system. `_pixel_to_pdf_coords()` handles coordinate conversion via the `is_normalized` parameter:

```python
def _pixel_to_pdf_coords(self, bbox, page_width, page_height, is_normalized=False):
    if is_normalized:
        # DeepSeek-OCR: 0-999 normalized coordinates
        x0 = bbox.x0 * page_width / 999
        y0 = bbox.y0 * page_height / 999
        x1 = bbox.x1 * page_width / 999
        y1 = bbox.y1 * page_height / 999
```

#### 1.3.3 Prompt Design

- DeepSeek-OCR: `DEEPSEEK_OCR_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."`
- VLM JSON: `VLM_JSON_SYSTEM_PROMPT` (7-rule JSON extraction prompt)

#### 1.3.4 Table Layout Optimization

`_compute_table_layout()` implements a row-height-priority iterative optimization algorithm:

- Default parameters: `font_size=9.0`, `single_line_height=font_size*1.2`, `min_col_ratio=0.1`, `max_col_ratio=0.5`
- Iteration control: `max_iterations=3`, `convergence_threshold=0.5`
- Each iteration recalculates row heights based on text content until the layout converges

### 1.4 Subprocess Isolation

`modules/ocr/ocr_worker.py` implements subprocess isolation to prevent PaddleOCR memory leaks from affecting the main process.

#### 1.4.1 Subprocess Environment Variables

```python
env = {
    'FLAGS_fraction_of_gpu_memory_to_use': '0.5',
    'KMP_DUPLICATE_LIB_OK': 'TRUE',
    'MKL_THREADING_LAYER': 'sequential',
}
# When no GPU is available
if not use_gpu:
    env['CUDA_VISIBLE_DEVICES'] = '-1'
```

#### 1.4.2 Parameter Degradation Strategy

`_degrade_params()` degrades parameters on each retry:

| Parameter | Degradation Rule |
|-----------|-----------------|
| Thread count | -1 |
| Memory factor | ×0.8 |
| Memory limit | ×0.8 |
| DPI | -20 (minimum 72) |
| Timeout | ×2.0 |
| Skip tables | Skip when attempt ≥ 1 |
| Skip formulas | Skip when attempt ≥ 2 |

#### 1.4.3 Retry Mechanism

`run_ocr_in_subprocess()` implements exponential backoff retry (×1.5), with `skip_pages` support for checkpoint resumption.

### 1.5 System-Adaptive Parameters

`OcrParameterCalculator` in `modules/ocr/system_profiler.py` automatically calculates OCR parameters based on system resources.

#### 1.5.1 Five-Level Memory Tiering

| Level | Memory Range | Memory Factor | Layout Limit | Table Limit | Formula Limit | DPI |
|-------|-------------|---------------|-------------|------------|--------------|-----|
| minimal | 0-8GB | 0.35 | 1000MB | 800MB | 500MB | 120 |
| low | 8-17GB | 0.45 | 1400MB | 1200MB | 800MB | 120 |
| medium | 17-33GB | 0.55 | 1800MB | 1600MB | 1000MB | 150 |
| high | 33-65GB | 0.60 | 2600MB | 2400MB | 1500MB | 150 |
| unlimited | 65GB+ | 0.65 | 3400MB | 3200MB | 2000MB | 200 |

#### 1.5.2 Model Selection

Each level corresponds to a different model scale:

| Level | Layout Model | Formula Model | OCR Model | Table Model |
|-------|-------------|---------------|-----------|-------------|
| minimal | PP-DocLayout-S | PP-FormulaNet_plus-S | PP-OCRv4_mobile | SLANet |
| low | PP-DocLayout-S | PP-FormulaNet_plus-S | PP-OCRv4_mobile | SLANet |
| medium | PP-DocLayout-M | PP-FormulaNet_plus-M | PP-OCRv4_server | SLANet_plus |
| high | PP-DocLayout-L | PP-FormulaNet_plus-L | PP-OCRv4_server | SLANet_plus |
| unlimited | PP-DocLayout-L | PP-FormulaNet_plus-L | PP-OCRv4_server | SLANet_plus |

When a GPU is available, the model level is automatically upgraded by one tier.

#### 1.5.3 High-Load Detection

When memory usage exceeds 85% or load average exceeds CPU cores ×0.8, high-load mode is triggered: thread count = `max(1, cpu//4)`, memory factor ×0.85.

---

## 2. Translation Pipeline Architecture

### 2.1 Triple Translator Design

| Translator | Class Name | Streaming | Retry | extra_body |
|------------|-----------|-----------|-------|------------|
| Aiping | `AipingTranslator` | `stream=True` | `max_retries=3` | `config.AIPING_EXTRA_BODY` |
| SiliconFlow | `SiliconFlowTranslator` | `stream=True` | `max_retries=0` | `config.SILICON_FLOW_EXTRA_BODY` |
| Baidu Qianfan | `QianfanTranslator` | `stream=True` | `max_retries=0` | `config.QIANFAN_EXTRA_BODY` |

All three share the base class `Translator` (`modules/translator.py`), with common parameters: `temperature=0.1`, `top_p=0.9`, `max_tokens` dynamically calculated (see 2.6). `QianfanTranslator` uses the Baidu Qianfan OpenAI-compatible API (default URL `https://qianfan.baidubce.com/v2`), authenticated via `QIANFAN_API_KEY`.

### 2.2 Four-Section Structured System Prompt

`Translator._generate_system_prompt()` generates a system prompt with a 4-section structure:

1. **Core Principles**: Semantic coherence, natural transitions, style consistency, conciseness
2. **Semantics & Style**: Terminology consistency, no additions or omissions, grammatical correctness, technical precision
3. **Preserve Formatting**: Do not translate URLs, preserve code formatting, length control, do not translate formulas, do not expand abbreviations, preserve list formatting, preserve cell delimiters `|||`
4. **No Meta-Annotations**: No meta-annotations or source text in output

The prompt is enhanced with language-specific rules injected via `rule_registry.merge_into_prompt()` (see Section 9 "Language-Specific Rule System"), enabling dynamic extension based on translation direction.

### 2.3 Preprocessing and Postprocessing

- **Same-language direct return**: When source and target languages are the same, translation is skipped
- **Empty text / `"..."` fallback**: For empty strings or ellipsis-only content, the original text is returned
- **Postprocessing**: `_postprocess_text()` cleans redundant markers from translation results

### 2.4 Truncation Detection

Both translators implement truncation detection:

```python
if finish_reason == "length":
    truncation_info = TruncationInfo(truncated=True, ...)
```

### 2.5 Streaming Response Processing

All three translators use `stream=True` for streaming calls, concatenating `delta.content` chunk by chunk. `AipingTranslator` additionally skips `reasoning_content` (reasoning content), only tracking its length for diagnostics:

```python
if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
    reasoning_length += len(chunk.choices[0].delta.reasoning_content)
    continue  # Skip reasoning content
```

The `format_blocks` typography call also uses streaming, but exceptions are not caught internally — they propagate to the caller `translation_content.py`, which reports to the UI via `task.add_warning` (see 11.3).

### 2.6 Dynamic max_tokens Calculation

Translators and layout models no longer use a fixed `max_tokens`; instead, it is dynamically calculated based on input text length:

```python
# Translator base class instance method
def _calculate_max_tokens(self, input_text, max_ceiling=None):
    estimated_tokens = len(input_text) / CHARS_PER_TOKEN  # CHARS_PER_TOKEN=3
    dynamic = max(MIN_OUTPUT_TOKENS, int(estimated_tokens * EXPANSION_FACTOR))  # EXPANSION_FACTOR=3, MIN_OUTPUT_TOKENS=256
    ceiling = max_ceiling if max_ceiling is not None else self.max_tokens
    return min(dynamic, ceiling)

# Standalone function (for non-Translator subclasses)
def calculate_max_tokens(input_text, max_ceiling, chars_per_token=3, expansion_factor=3, min_output_tokens=256):
    ...
```

- **Translation calls**: All three translators use `self._calculate_max_tokens(text)`, with ceiling of `self.max_tokens` (default 8192)
- **Layout calls**: `format_blocks` uses `self._calculate_max_tokens(blocks_text, max_ceiling=config.LAYOUT_MAX_TOKENS)`; `MarkdownGenerator` uses `calculate_max_tokens(user_prompt, self.max_tokens)`

### 2.7 Translation Quality Detection and Retry

#### 2.7.1 Untranslated Detection

`_is_translation_unchanged` uses a dual strategy to detect when the LLM has not translated the text:

1. **Original strategy**: `|||` segment detection — splits the translation by `|||` and checks whether all segments come from the original text
2. **New strategy**: High similarity + no target language characters — after removing hyphenation markers, calculates normalized similarity >85% and the translation contains no target language (default: Chinese CJK) characters

Helper methods:
- `_normalize_for_comparison`: Removes soft hyphenation markers and excess whitespace
- `_calculate_similarity`: Uses LCS for short text (≤500 characters), character set intersection approximation for long text
- `_contains_target_language_chars`: Detects whether text contains CJK Unified Ideographs (U+4E00-U+9FFF)

#### 2.7.2 Garbage Output Detection

`_is_translation_garbage` detects abnormal LLM output:

- **Expansion detection**: Translation length > original length × 5
- **Repetition pattern detection**: Same substring (2-50 characters) repeated consecutively > 10 times

#### 2.7.3 Automatic Retry

In merged and original block translation flows, when untranslated text is detected, an automatic retry is performed once:

```python
if self._is_translation_unchanged(translated_text, original_text):
    retry_result = translator.translate(original_text, ...)
    if not self._is_translation_unchanged(retry_result.content, original_text):
        translated_text = retry_result.content  # Retry succeeded
    else:
        translated_text = original_text  # Retry failed, fall back to original text
```

Garbage output detection runs after truncation detection, covering both normal and truncated scenarios; when detected, it falls back to original text directly.

### 2.8 Format Blocks Toggle

Post-translation LLM format blocks is controlled by the `ENABLE_FORMAT_BLOCKS` configuration:

| Value | Behavior |
|-------|----------|
| `false` (default) | No format blocks |
| `true` | Always execute format blocks |
| `auto` | Execute format blocks only when output includes PDF (`output_format` is `pdf`/`pdf_docx`/`all`) |

The `_translate_content` method receives an `output_format` parameter, combined with `config.ENABLE_FORMAT_BLOCKS` to determine whether to execute the format blocks step.

---

## 3. Semantic Merging Strategy

### 3.1 Rule-Based Merging

`merge_semantic_blocks()` (in `utils/text_processing.py`) uses rules to determine whether text blocks should be merged:

**Merge conditions** (all must be satisfied):
- Vertically adjacent (distance < 10px)
- At least one of the following:
  - Has section information
  - Previous block does not end with a complete sentence
  - Current block is a sentence continuation

**Forced split conditions**:
- Between section headings and body text
- Between different sections
- Alignment change
- Formula blocks remain standalone

**Space handling**: Intelligently adds a space when merging — inserts one space when the previous block does not end with a space and the following block does not start with one.

### 3.2 LLM-Based Merging

`merge_semantic_blocks_with_llm()` uses a semantic analyzer to batch-determine merge relationships:

- Batch size: `batch_size=10`
- Each batch includes the previous block's text as context
- On analysis failure, the current batch is skipped

### 3.3 Two-Phase Parallel Merging

`merge_semantic_blocks_with_llm_two_phase()` implements a two-phase architecture:

**Phase 1**: Parallel LLM calls to obtain merge decisions for all text pairs

- Uses the `parallel_batch_analyze()` function
- Overlap-1-block batch strategy: adjacent batches overlap by 1 block, ensuring boundary pairs are also analyzed
- Parameters: `max_workers=5`, `batch_size=20`, `max_retries=3`
- On batch failure, returns `[False] * (len(batch) - 1)` as default values

**Phase 2**: Sequential merging based on pre-stored decision results

### 3.4 Semantic Role Analysis

`SemanticAnalyzer` (`modules/semantic_analyzer.py`) implements a two-step analysis:

1. **Semantic Role Identification**: Classifies text blocks as body, title, signature, list_item, quote_body
2. **Merge Decision Matrix**:

| Previous Role | Next Role | Decision |
|--------------|-----------|----------|
| body | body | Further check |
| body | title | Do not merge |
| body | signature | Do not merge |
| body | list_item | Further check |
| title | * | Mostly do not merge |
| signature | * | Never merge |
| list_item | list_item | Continuity check |

Fault tolerance: 3 retries; when result count mismatches, fill with `False`; on JSON parse failure, return `[False] * count`.

### 3.5 Translation Result Splitting

`split_translated_result()` splits merged translation results back according to the original text block length ratios:

- Minimum characters per block: `min_characters_per_block=3`
- Split position adjustment: `adjust_split_position()` ensures English word integrity, punctuation does not start a block, and left-paired characters do not end a block
- Empty block repair: borrows content from adjacent blocks
- Final checks: block-start punctuation adjustment + block-end left-paired character fix

---

## 4. PDF Generation Technology

### 4.0 Renderer Split

The rendering logic of `PdfGenerator` (`modules/pdf_generator.py`) has been split into two independent modules:

- `modules/pdf_text_renderer.py` (`PdfTextRenderer`): Handles text rendering, including the two-pass drawing strategy, font selection chain, font size estimation, line height ratio calculation, and text overflow handling
- `modules/pdf_table_renderer.py` (`PdfTableRenderer`): Handles table rendering, including the table two-pass strategy, merged cell processing, visible segment computation, and dynamic cell font size calculation

After the split, `PdfGenerator` serves as a facade class coordinating the two renderers, keeping the external interface unchanged.

### 4.1 Two-Pass Rendering Strategy

`PdfGenerator._draw_translated_text()` (in `modules/pdf_generator.py`) uses a two-pass rendering approach:

**First pass**: Add redaction annotations to mark original text regions for removal

```python
page.add_redact_annot(bg_rect, fill=(1, 1, 1))
# ...
page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
```

- Horizontal padding: `h_padding = max(5, min(font_size * 0.5, 12))`
- Vertical padding: `v_padding = max(3, min(font_size * 0.3, 6))`
- `images=fitz.PDF_REDACT_IMAGE_NONE` ensures images are not removed

**Second pass**: Render translated text using the original text style

### 4.2 Font Selection Chain

`_get_suitable_font()` selects fonts by priority:

1. Check if the original font supports the target language (`_check_embedded_font_support()`)
2. Look for Arial Unicode font (general multilingual support)
3. Iterate through system fonts to find a compatible font (`_check_font_support()`)
4. Throw `ValueError` when no suitable font is found

Font caching: `font_cache` caches lookup results keyed by `(original_font, target_lang)`, avoiding repeated filesystem lookups.

### 4.3 Font Size Estimation

When `font_size == 0` (e.g., LLM OCR without style information), the size is estimated from the bbox height:

```python
if original_font_size == 0:
    original_font_size = min(bbox_height * 0.75, 36)
```

### 4.4 Line Height Multiplier Calculation

```python
estimated_lines = max(1, round(bbox_height / (font_size * 1.2)))
original_lineheight = bbox_height / (font_size * estimated_lines)
original_lineheight = max(1.0, min(original_lineheight, 2.0))
```

### 4.5 Formula Rendering Degradation Chain

`_render_formula_image()` implements a four-level degradation:

| Level | Method | Description |
|-------|--------|-------------|
| 1 | usetex | Used when LaTeX is installed system-wide; supports full LaTeX commands |
| 2 | mathtext raw | Attempt mathtext rendering with raw LaTeX |
| 3 | mathtext preprocessed | Render after preprocessing with `_preprocess_latex_for_mathtext()` |
| 4 | Return None | Rendering completely failed; falls back to plain text |

LaTeX availability detection (`_check_latex_available()`) uses dual detection: first checks PATH, then probes common installation paths (macOS/Linux/Windows). The result is cached in the class variable `_latex_available`.

### 4.6 LaTeX Preprocessing

`_preprocess_latex_for_mathtext()` performs the following conversions:

1. `\(...\)` → `$...$`, `\[...\]` → `$$...$$`
2. `$$...$$` → `$...$` (mathtext does not support display math)
3. Remove math font commands: `\text{}`, `\mathrm{}`, `\mathbf{}`, etc.
4. Remove environment wrappers: `\begin{aligned}...\end{aligned}`, etc.
5. Greek letter substitution: `\alpha` → `α`, `\beta` → `β`, etc.
6. Math symbol substitution: `\circ` → `°`, `\cdot` → `·`, etc.
7. Remove `\left` and `\right` commands

### 4.7 Mixed Formula-Text Rendering

`_render_mixed_text_formula_image()` handles non-formula text blocks containing LaTeX formula fragments, following the same usetex → mathtext degradation chain.

### 4.8 Text Overflow Handling

`_draw_translated_text()` implements five-level overflow handling:

1. **Font reduction** (5 attempts): Reduce by 10% each time, no smaller than 70% of original size
2. **Extreme reduction**: Reduce to 60% and 50%
3. **Line height adjustment**: Try lineheight=1.5, 1.8, 2.0
4. **Smart truncation**: Truncate at word boundaries (English) or by character count (CJK), preserving at least 30%
5. **Mechanical truncation**: Truncate 10% at a time, preserving at least 30%

### 4.9 Table Drawing

`_draw_translated_table()` also uses the two-pass strategy (redaction + insertion), and implements:

- Skip drawing internal grid lines within merged cells
- `_compute_visible_segments()` calculates visible line segments
- Dynamic cell font size calculation: `base_font_size = min(cell_height * 0.8, 12)`
- `estimated_lines` pre-evaluates cell capacity

### 4.10 Document Compression

Compression optimization is enabled when saving:

```python
new_doc.save(output_pdf_path, deflate=True, garbage=4, clean=True)
```

---

## 5. DOCX Generation Technology

### 5.1 LaTeX → MathML → OMML Conversion Chain

`DocxGenerator` (`modules/docx_generator.py`) implements LaTeX formula to Word OMML conversion:

1. LaTeX font command preprocessing: remove `\mathsf`, `\mathrm`, `\mathbf`, `\mathit`, `\mathcal`, `\mathbb`, `\mathfrak`, `\mathscr`, `\mathtt`
2. `latex2mathml` library converts LaTeX to MathML
3. `_mathml_to_omml_element()` converts MathML to Office Math Markup Language (OMML)

### 5.2 OMML Element Processing

`_make_mr()` and related methods handle the following OMML elements:

| MathML Element | OMML Element | Description |
|---------------|-------------|-------------|
| math | oMath | Math region |
| mrow | r | Row |
| mstyle | r | Style |
| mi | r | Identifier (variable name) |
| mo | r | Operator |
| mn | r | Number |
| mtext | r | Text |
| mfrac | f | Fraction |
| msup | sSup | Superscript |
| msub | sSub | Subscript |
| msubsup | sSubSup | Sub-superscript |
| msqrt | rad | Square root |
| mover | acc | Overscript |
| munder | sSub | Underscript |

### 5.3 Table Processing

- Fixed layout: `MAX_TABLE_WIDTH_INCHES = 6.5`
- Column widths: distributed according to original PDF proportions
- Row heights: obtained from original PDF data
- Merged cells: `word_table.cell().merge()`
- Cell alignment: left/center/right alignment

### 5.4 Chart Positioning

`_find_chart_position()` and `_find_merged_block()` locate chart positions within original text blocks by y-coordinate, determining insertion points.

### 5.5 XML Compatibility

`_clean_xml_compatible_text()` cleans incompatible characters from text, retaining printable ASCII (32-126), tab/newline/carriage return (9/10/13), and Unicode characters (128+).

---

## 6. Markdown Generation Technology

### 6.1 LLM-Driven Formatting

`MarkdownGenerator` (`modules/markdown_generator.py`) uses an LLM to format translated text into structured Markdown:

- `_format_with_layout_model()` invokes the layout model
- `_load_layout_prompt()` loads the formatting prompt template
- The layout prompt includes 6 rules: content structure, emphasis, formatting conventions, no code block markers, preserve images, preserve math formulas

### 6.2 Formula Protection Placeholders

`_format_with_layout_model()` protects formula content before calling the LLM:

1. Extract formulas and replace with `__FORMULA_N__` placeholders
2. Replace display math `$$...$$` first, then inline math `$...$`
3. After the LLM responds, restore placeholders to original formulas

```python
text_for_llm = re.sub(r'\$\$(.+?)\$\$', replace_formula, text, flags=re.DOTALL)
text_for_llm = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', replace_formula, text_for_llm)
```

### 6.3 Truncation Detection

```python
truncated = finish_reason == "length"
```

### 6.4 Chapter-Split Parallel Generation

`_generate_chapter_markdowns()` uses `ThreadPoolExecutor(max_workers=config.MAX_WORKERS)` to generate Markdown for each chapter in parallel.

### 6.5 Aiping Variant

`AipingMarkdownGenerator` overrides the `_call_api()` method, using `extra_body=config.AIPING_EXTRA_BODY`.

### 6.6 Factory Function

```python
create_markdown_generator(api_type, api_key, api_url, model)
```

Creates the corresponding Markdown generator instance based on `api_type`.

---

## 7. Table Processing Pipeline

### 7.1 Dual-Engine Extraction

#### 7.1.1 Camelot Extraction (Non-OCR)

`extract_tables_by_camelot()` (in `modules/extractors/table_processor.py`) uses the Camelot library to extract tables:

- Prefers `lattice` mode (line-based detection)
- Falls back to `stream` mode (whitespace-based detection) on failure
- Coordinate system conversion: `convert_pdf_to_pymupdf_coords()` converts PDF standard coordinates (origin at bottom-left) to PyMuPDF coordinates (origin at top-left)

#### 7.1.2 PyMuPDF Extraction (Non-OCR)

`extract_tables_by_pymupdf()` uses PyMuPDF's built-in table detection, supporting precise cell bboxes.

### 7.2 Precise Character Assignment

`extract_table_cells_by_bbox()` assigns characters to cells using a 50% area overlap criterion:

1. Obtain character-level data from `page.get_text("rawdict")`
2. Table bbox filtering: 2px tolerance, excluding characters outside the table
3. For each character, calculate the intersection area with each cell
4. Assign to a cell only when overlap exceeds 50%
5. Sort characters by reading order (y-coordinate → x-coordinate) and concatenate

### 7.3 Merged Cell Inference

`compute_span_from_none_positions()` (in `modules/extractors/coordinate_utils.py`) infers merged cells from None positions returned by PyMuPDF:

1. Scan horizontally for consecutive None positions in the same row to determine col_span
2. Mark None positions covered by col_span
3. Scan vertically to determine row_span, skipping None positions already covered by col_span
4. Re-validate col_span based on row_span

### 7.4 Grid Layout Calculation

- `calculate_row_heights_from_bboxes()`: Infers row heights from actual cell bboxes, taking the maximum height in each row
- `calculate_col_widths_from_bboxes()`: Infers column widths from actual cell bboxes; merged cell widths are evenly distributed across spanned columns, then proportionally scaled so the total equals the actual table width

### 7.5 Alignment Detection

- `extract_cell_alignment()`: Text center offset from cell center < 15% → centered; left edge offset < 10% → left-aligned; right edge offset < 10% → right-aligned
- `detect_text_block_alignment()`: Left/right alignment takes priority over center detection; wide blocks (>55% page width) are classified as left-aligned

### 7.6 OCR Table Processing

PaddleOCR: `_TableHtmlParser` parses HTML-format tables; `_compute_table_grid()` calculates grid layout based on textlines.

LLM OCR: `_compute_table_layout()` implements row-height-priority iterative optimization (see 1.3.4); `_parse_html_table()` parses HTML tables.

---

## 8. Formula Detection and Rendering

### 8.1 Detection Rules

`LlmOcrExtractor._detect_formula()` detects formulas in the following formats:

- Display math: `$$...$$`
- Inline math: `$...$`
- LaTeX delimiters: `\(...\)`, `\[...\]`
- LaTeX math environments: aligned, gathered, cases, equation, align, gather, matrix variants

### 8.2 LaTeX Cleaning

`PaddleOcrExtractor._clean_latex()` cleans LaTeX output from PaddleOCR:

- Remove excessive escaping
- Fix common OCR errors
- Standardize formula formatting

### 8.3 Multi-Level Rendering Degradation

Formula rendering degradation chain in PDF output (see 4.5 for details):

```
usetex → mathtext raw → mathtext preprocessed → skip (plain text)
```

Formula conversion chain in DOCX output:

```
LaTeX → MathML → OMML (Word native formula format)
```

Formula protection in Markdown output:

```
$$...$$ / $...$ → __FORMULA_N__ placeholder → LLM processing → restore original formula
```

### 8.4 Mixed Formula Text

`PdfGenerator._contains_latex_formula()` detects LaTeX fragments in non-formula text blocks, and `_render_mixed_text_formula_image()` renders the mixed text as a whole.

---

## 9. Language-Specific Rule System

### 9.1 Rule Registry

`PromptRuleRegistry` (`prompts/rule_registry.py`) is a singleton registry for language-specific rules, responsible for finding and injecting additional prompt rules based on translation direction (source language → target language).

Core methods:

- `merge_into_prompt(base_prompt, source_lang, target_lang)`: Appends matching language-specific rules to the end of the base prompt, returning the enhanced complete prompt
- `register(source_lang, target_lang, rules)`: Registers a language-specific rule

### 9.2 Rule File Organization

```
prompts/
├── __init__.py                 # Module initialization
├── rule_registry.py            # PromptRuleRegistry — rule registry (singleton)
└── language_rules/             # Language-specific rules directory
    ├── __init__.py             # Auto-discovery and registration of rules
    ├── base.py                 # Common base rules
    └── bo_to_zh.py             # Tibetan→Chinese specific rules
```

### 9.3 Rule Auto-Discovery

`language_rules/__init__.py` automatically scans rule files in the same directory on module load, calling `rule_registry.register()` to complete registration. Adding a new language-specific rule only requires creating a rule file in the `language_rules/` directory and implementing registration — no other code modifications needed.

### 9.4 Existing Rules

| Source Language | Target Language | Rule File | Description |
|----------------|----------------|-----------|-------------|
| — | — | `base.py` | Common base rules, applicable to all translation directions |
| `bo` | `zh` | `bo_to_zh.py` | Tibetan→Chinese specific rules, handling Tibetan-specific translation issues |

---

## 10. Glossary Extraction and Chapter Identification

### 10.1 Glossary Extraction

#### 10.1.1 Dual Extractor Design

`modules/glossary_extractor.py` defines an abstract base class and two implementations:

| Extractor | Class Name | extra_body | Timeout |
|-----------|-----------|------------|---------|
| Aiping | `AipingGlossaryExtractor` | `config.AIPING_EXTRA_BODY` | 30s |
| SiliconFlow | `SiliconFlowGlossaryExtractor` | `config.SILICON_FLOW_EXTRA_BODY` | 30s |

Factory function: `create_glossary_extractor(extractor_type)`, supporting `'aiping'` and `'silicon_flow'` types.

#### 10.1.2 NO_GLOSSARY Sentinel Value

When the LLM determines there are no specialized terms in the text, it returns the `NO_GLOSSARY` identifier. The `_format_glossary()` method skips lines containing `NO_GLOSSARY`.

#### 10.1.3 Extraction Rules

The prompt includes the following core rules:
- Extract only genuine specialized terms from the specified domain
- Exclude common words, everyday expressions, personal names, place names, and company names
- Preserve established conventions as-is (AI, ML, LLM, ChatGPT, etc.)
- Do not provide translations when source and target languages are the same
- Extract each term only once
- Input text is truncated to the first 5000 characters

#### 10.1.4 Output Format

One term per line, in the format `term: translation`.

### 9.2 Chapter Identification

#### 9.2.1 Bookmark Extraction

`ChapterIdentifier` (`modules/chapter_identifier.py`) builds a chapter tree from PDF bookmarks:

```python
bookmarks = doc.get_toc(simple=False)
chapters = self._build_chapter_tree(bookmarks, doc)
```

#### 10.2.2 Title Location

`_locate_title_blocks()` finds text blocks in pages corresponding to chapter titles, using a three-level matching strategy:

1. **Exact match** (score=100): Text is identical
2. **High-similarity match** (score=90+): `difflib.SequenceMatcher` similarity > 0.9
3. **Substring match** (score=50): Title is a substring of the text
4. **Cross-block match** (score=80+): Merge up to 3 consecutive text blocks

#### 9.2.3 Chapter Tree Construction

`_build_chapter_tree()` uses a stack structure to build hierarchical relationships:

- Maximum depth: `max_level=3`
- Title truncation: `max_title_length=20`, with `...` appended when exceeded

#### 10.2.4 Default Chapters

When the beginning of a PDF has pages not covered by bookmarks, `_create_default_chapters()` creates default chapters:

- Smart naming (`use_smart_naming=True`): Uses the first text block on the page as the title
- Fallback naming: `{filename}-Page{page_number}`

#### 10.2.5 Element Association

- `associate_text_blocks()`: Associates text blocks with corresponding chapters
- `associate_tables()`: Associates tables with corresponding chapters
- `associate_images()`: Associates images with corresponding chapters

Association algorithm: `_find_best_chapter()` finds the best-matching chapter based on page number and y-coordinate.

---

## 11. Error Handling and Retry Mechanisms

### 11.1 OCR Three-Layer Protection

`modules/ocr/ocr_worker.py` implements a three-layer protection mechanism:

| Layer | Mechanism | Parameters |
|-------|-----------|------------|
| Heartbeat monitoring | `_heartbeat_sender()` | 15-second interval (`stop_event.wait(15)`) |
| Stall detection | Timeout check | Dynamic timeout = `avg_time_per_page × 1.5` |
| Total timeout | Global timeout | User-configured timeout |

#### 11.1.1 Heartbeat Timeout

The main process monitors the subprocess heartbeat; heartbeat timeout triggers a retry.

#### 11.1.2 Stall Detection

`_run_ocr_once()` detects processing stalls: if the current page processing time exceeds 1.5× the average time, it is considered stalled.

#### 11.1.3 Partial Result Preservation

On timeout or error, successfully extracted page results are preserved. The `skip_pages` parameter allows skipping already-processed pages on retry.

### 11.2 OCR Parameter Degradation

Parameters degrade on each retry (see 1.4.2 for details), progressively reducing resource consumption to improve success rate.

### 11.3 Translation Retry & Error Classification

- Aiping: `max_retries=3`, exponential backoff
- SiliconFlow: `max_retries=0` (no SDK retry)
- Baidu Qianfan: `max_retries=0` (no SDK retry)
- All translators catch exceptions and classify them via `classify_llm_error(e)` from `modules/llm_error_handler.py`, mapping to Chinese user-friendly messages (e.g. authentication failed / rate limit / request timeout / internal server error); on timeout, a warning is logged and the current text block is skipped without interrupting the overall flow
- `format_blocks` typography call exceptions are no longer swallowed internally — they propagate to `translation_content.py`, which reports to the UI via `task.add_warning` using `classify_llm_error` for friendly messages

### 11.4 Semantic Analysis Fault Tolerance

- 3 retries
- Fill with `False` when result count mismatches
- Return `[False] * count` on JSON parse failure
- Skip the current batch on batch analysis failure

### 11.5 Generation Degradation

#### 11.5.1 PDF Formula Rendering Degradation

```
usetex → mathtext raw → mathtext preprocessed → plain text
```

#### 10.5.2 PDF Text Overflow Degradation

```
Font reduction → Extreme reduction → Line height adjustment → Smart truncation → Mechanical truncation
```

#### 11.5.3 Markdown Generation Degradation

On layout model request failure, retry 3 times (`max_retries=3`, `retry_delay=2s`); throw an exception on final failure.

### 11.6 PPStructureV3 Log Pollution Fix

`PaddleOcrExtractor._restore_logger_state()` saves and restores logger configuration before and after OCR processing, preventing PPStructureV3 from modifying the global log level.

---

## 12. Progress Management Model

### 12.1 Seven-Phase Progress Configuration

`PHASE_CONFIG` (`models/phase_config.py`) defines 7 phases for translation tasks:

| Phase | ID | Name | Progress Range |
|-------|-----|------|---------------|
| 1 | init | Initialization | 0-5 |
| 2 | extraction | Text and chart extraction | 5-40 |
| 3 | semantic_merge | Semantic merging | 40-50 |
| 4 | translation | Text translation | 50-85 |
| 5 | table_translation | Table translation | 85-92 |
| 6 | generation | Output generation | 92-98 |
| 7 | clean | Cleanup temporary files | 98-100 |

### 12.2 Glossary Extraction Three-Phase Configuration

`GLOSSARY_PHASE_CONFIG` defines 3 phases for glossary extraction tasks:

| Phase | ID | Name | Progress Range |
|-------|-----|------|---------------|
| 1 | init | Start extraction | 0-5 |
| 2 | pdf_extraction | Text extraction | 5-30 |
| 3 | term_extraction | Term extraction | 30-100 |

### 11.3 Task State Machine

`Task` (`models/task.py`) inherits `CopyableMixin`, with state transitions:

```
pending → processing → completed
                    → error
                    → canceled
```

State enum: `TASK_STATUS = {'PENDING': 'pending', 'PROCESSING': 'processing', 'COMPLETED': 'completed', 'ERROR': 'error'}`

### 11.4 Progress Update

- `update_progress(progress, message)`: Directly sets overall progress (0-100)
- `update_phase_progress(phase, phase_percent, message)`: Calculates overall progress by phase

Mapping from within-phase progress to overall progress:

```python
overall_progress = start + round((end - start) * phase_percent / 100)
```

### 12.5 Thread Safety

`Task` uses `threading.RLock()` to protect all state mutation operations, ensuring data consistency in multi-threaded environments.

### 11.6 Task Types

`set_task_type(task_type)` switches the task type:

- `'translation'`: Uses `PHASE_CONFIG`
- `'glossary'`: Uses `GLOSSARY_PHASE_CONFIG`

### 11.7 Cancellation Mechanism

The `cancel()` method sets `canceled=True`. `update_progress()` and `update_phase_progress()` return `False` after cancellation, stopping progress updates.

### 11.8 Configuration Validation

`validate_phase_config()` validates phase configuration:

- Each phase must have start and end
- start and end must be numeric
- Ranges must be within 0-100
- start must be less than end
