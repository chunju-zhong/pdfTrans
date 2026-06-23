# Changelog

## 2026-06-23

- OCR configuration cleanup and rename:
  - **Removed `OCR_DPI`**: This config item was never referenced by any code (legacy artifact), removed from `config.py`
  - **Renamed `OCR_RENDER_DPI` → `OCR_PADDLE_DPI`**: Symmetric naming with `OCR_LLM_DPI`, clearly indicating it's the PaddleOCR engine-specific DPI config
  - Affected scope: `config.py`, `modules/ocr/paddle_extractor.py` (3 references)
- SKILL.md documentation update — added LLM OCR feature documentation:
  - Updated `--ocr-engine` parameter description to show both `paddleocr` and `llm` options
  - Added LLM OCR engine feature description (working principle, supported models, response formats, feature list)
  - Added LLM OCR environment variable configuration (e.g., `AIPING_OCR_LLM_MODEL`, `OCR_LLM_DPI`)
  - Added LLM OCR usage examples and notes
- Files changed: `config.py`, `modules/ocr/paddle_extractor.py`, `SKILL.md`

## 2026-06-22

- LLM OCR title-type text blocks not translated fix:
  - **BLOCK_TYPE_MAP mapping error**: `title`, `sub_title`, `section_title` were mapped to `is_body_text=False`, and the translation service only translates blocks with `is_body_text=True`, causing all title-type text blocks to be skipped, leaving titles untranslated in the output PDF. Fixed by changing `is_body_text` to `True` for these three title types, while keeping `block_type_int=1` unchanged
  - Affected scope: LLM OCR mode only; headers, footers, etc. remain `is_body_text=False`
- Files changed: `modules/ocr/llm_extractor.py`

## 2026-06-22

- PaddleOCR table content not displaying fix (3 items):
  - **Table bbox not added to processed_pixel_bboxes**: During PaddleOCR extraction, table bbox was not marked as processed, causing 73 textlines inside the table to be misidentified as "uncovered", creating 20 supplement TextBlocks that were then blacked out by table redaction. Fixed by adding table bbox to `processed_pixel_bboxes`
  - **estimated_lines not calculated**: PaddleOCR `_compute_table_grid()` did not set `estimated_lines`, preventing the drawing phase from pre-judging cell capacity to reduce font size early. Fixed by calculating and setting `estimated_lines` for each cell with text
  - **estimate_text_display_width extracted as shared function**: Extracted from `llm_extractor.py` to `coordinate_utils.py`, `llm_extractor.py` now imports it
- PDF generator table truncation fix:
  - **Cell text repeated overlay**: Binary search truncation appended text on each successful `insert_textbox` call (PyMuPDF doesn't overwrite previous results), causing 4-5 overlapping texts in the same cell. Fixed by switching to linear decrement loop (break on success), consistent with the 5-attempt shrink loop logic, writing only once
- PDF generator white background fix:
  - **Restore white background**: `add_redact_annot` `fill` changed from transparent `None` back to white `(1,1,1)`, ensuring translated text effectively covers original text (transparent background caused overlap of original and translated text, reducing readability; will optimize to match original background color once reliable text color extraction method is found)
  - Affected scope: text block and table cell redaction calls
- Files changed: `modules/pdf_generator.py`, `modules/ocr/paddle_extractor.py`, `modules/extractors/coordinate_utils.py`, `modules/ocr/llm_extractor.py`

## 2026-06-21

- Python code review fixes (12 items, covering HIGH/MEDIUM/LOW severity):
  - **HIGH**: LaTeX environment regex now uses capture group + backreference, ensuring `\begin{aligned}...\end{cases}` is not incorrectly matched
  - **HIGH**: Fallback `\\` and `&` replacements made conditional (lookahead/lookbehind), avoiding damage to legitimate LaTeX content
  - **HIGH**: `_check_latex_available` PATH modification moved inside `_latex_lock`, fixing thread safety issue
  - **MEDIUM**: `_parse_html_table` return value check changed from `if cells:` to `if cells is not None:`, preventing empty matrix misjudgment
  - **MEDIUM**: `_estimate_text_display_width` expanded CJK width estimation with Japanese Hiragana/Katakana and Korean Hangul
  - **MEDIUM**: Table cell text truncation optimized from linear search to binary search, reducing `insert_textbox` calls from O(n) to O(log n)
  - **MEDIUM**: `_compute_table_layout` docstring now documents side effect of modifying `matrix` parameter
  - **MEDIUM**: `docx_generator.py` merge cell exception catch narrowed from `Exception` to `(ValueError, KeyError)`
  - **LOW**: `llm_extractor.py` module-level import order fixed, constant `TABLE_HTML_MARKER` moved after imports
  - **LOW**: `_check_latex_available` LaTeX path detection now supports Linux and Windows, using `sys.platform` conditional
- PDF generator optimizations (4 items):
  - **Transparent background**: `add_redact_annot` `fill` changed from white `(1,1,1)` to `None`, avoiding covering non-white backgrounds
  - **Table bbox fallback**: In `_draw_translated_table`, when `table_bbox` is None, use page area as fallback to avoid `table_x0` undefined error
  - **Cell capacity pre-check**: Pre-judge cell capacity based on `estimated_lines`, reduce font size early to prevent text overflow
  - **amsmath package**: Load `\usepackage{amsmath}` in usetex mode, supporting `\begin{aligned}` and other environments
- Word generator optimizations (3 items):
  - **Merged cell column count**: Calculate logical column count considering `col_span` when creating tables, avoiding insufficient columns
  - **Column width boundary check**: Check `col_idx < len(word_table.columns)` when setting column widths, avoiding index out of range
  - **Skip over-column cells**: Skip cells beyond Word table column count when filling cell content
- Data model extension:
  - `PdfCell` new `estimated_lines` field, supporting estimated text line count
- Utility function added:
  - `fix_line_break_hyphens()`: Fix line-break hyphens in OCR output (e.g., "his- torical" → "historical")
- Files changed: `modules/pdf_generator.py`, `modules/ocr/llm_extractor.py`, `modules/docx_generator.py`, `models/extraction.py`, `utils/text_processing.py`

## 2026-06-19

- Fixed multiple LLM OCR table rendering and positioning issues:
  - **Table HTML rendered as plain text**: In JSON/ref-tag/Markdown response formats, text blocks containing `<table>` were also rendered as TextBlocks, causing raw HTML strings in PDF output. Added filtering logic to skip text blocks containing table HTML
  - **Table content not translated**: Logic inversion bug in `_extract_tables_from_text` — `if not cells:` condition caused only empty tables to be added while populated tables were skipped. Fixed to `if not cells: continue`
  - **`table_x0` undefined error**: In `_draw_translated_table`, variables were unassigned when `table_bbox` was None. Added else branch using page area as fallback
  - **Table position fixed, not following original PDF**: DeepSeek-OCR `<|ref|>` tag's `<|det|>` table coordinates were discarded by code, replaced with hardcoded estimated positions. Fixed to preserve det coordinates and pass via `table_bbox_map` to `_extract_tables_from_text`
  - **Multiple tables overlapping**: All tables on the same page started at y=100pt. Fixed to offset each subsequent table based on the previous table's bottom y coordinate
- Fixed LLM OCR extraction progress bar not updating:
  - Added `progress_callback` parameter to `extract_from_pdf`, sending `step_start`/`step_progress`/`step_complete` callbacks per page
  - `pdf_extractor.py` LLM OCR branch now passes `progress_callback`
- Code review optimizations (4 items):
  - **HIGH**: Changed `table_bbox_map` from HTML full-text key to integer index key, avoiding whitespace mismatch failures
  - **MEDIUM**: Eliminated duplicate `table_bbox` deconstruction in `_parse_html_table`, moved to before loop
  - **MEDIUM**: Eliminated redundant bbox validity check in `_extract_tables_from_text`
  - **LOW**: Extracted `'<table'` as module-level constant `TABLE_HTML_MARKER`
- Files changed: `modules/ocr/llm_extractor.py`, `modules/pdf_extractor.py`, `modules/pdf_generator.py`, `tests/test_llm_ocr.py`

## 2026-06-18

- Fixed short text untranslated detection bypass — LLM self-added `|||` separator causing untranslated text to evade detection:
  - **Lowered aiping translator temperature**: `temperature` reduced from `0.7` to `0.1`, `top_p` adjusted from `0.8` to `0.9`, matching siliconflow translator parameters to reduce LLM creative output (self-adding unexpected format symbols)
  - **Added smart untranslated detection function**: `_is_translation_unchanged()` — detects scenarios where LLM adds `|||` to original text without actually translating (e.g., `"Effluent standard Separation option"` → `"Effluent standard ||| Separation option"`), by stripping separators and checking each segment against source text
  - **Upgraded two detection points**: `translate_original_block()` and `translate_merged_block()` post-translation verification upgraded from simple `==` comparison to new function call, with enhanced logging showing first 200 chars of result for easier debugging
  - **Added unit tests**: 5 test cases covering `|||`-wrapped untranslated, normal translation, normal translation with `|||`, exact match, and empty string scenarios — all 11/11 tests passing
  - Root cause: Three factors combined — system prompt Rule 16 `|||` concept leakage + temperature=0.7 too high + input text being two bare noun phrases with special structure
  - Files changed: `modules/aiping_translator.py`, `services/translation_service.py`, `tests/test_translation_service.py`

## 2026-06-14

- Translation prompt optimizations (3 changes):
  - **Extended Rule 10 to "Code Block Preservation & Formatting"**: Added code formatting requirements (preserve indentation, spacing, newlines, alignment), code feature detection with keywords and symbols, and comment non-translation rule
  - **Fixed Rule 10 feature description**: Removed "consecutive multi-line indented text" and "special indentation structures" (newlines are already stripped at extraction stage, multi-line structure no longer exists in LLM input); kept only keyword and symbol features for code detection
  - **Strengthened Rule 14 to "No Meta-Comments or Source Text Output"**: Added "strictly forbid outputting source text" and "do not retain original text" to prevent LLM from outputting both original and translated text
- Refined newline cleanup strategy: Changed `\n` replacement from empty string to space across all extraction paths (`text.replace('\n', '')` → `text.replace('\n', ' ')`), preventing adjacent word concatenation after newline removal
- Updated test assertion to match new rule text
- Files changed: `modules/translator.py`, `modules/ocr/paddle_extractor.py`, `modules/pdf_extractor.py`, `modules/extractors/coordinate_utils.py`, `tests/test_newline_preservation.py`

## 2026-06-13

- Centralized newline deletion at extraction stage — all newline cleanup moved to extraction phase:
  - `_build_text_from_textlines`: Delete `\n` directly (replace with empty string) for all text blocks
  - `_extract_text_blocks`: Delete `\n` directly during text block construction
  - Table cell creation: Delete `\n` directly in cell text (in `coordinate_utils.py`)
- Removed scattered newline handling from other pipeline stages:
  - Translation pre/post processing no longer handles newlines
  - System prompt no longer includes newline-related instructions
- Removed "Maintain Newline Consistency" rule from translation prompt (previously added 2026-06-12)
- Changed strategy: delete newlines directly (replace with empty string) rather than replace with spaces — cleaner removal without introducing extra whitespace
- Files changed: `modules/ocr/paddle_extractor.py`, `modules/pdf_extractor.py`, `modules/extractors/coordinate_utils.py`, `modules/translator.py`

## 2026-06-12

- Added "Maintain Newline Consistency" rule to translation prompts — resolved translation results adding newlines causing text box overflow:
  - Added 7th rule in `modules/translator.py` `_generate_system_prompt` method
  - Rule content: Preserve newlines if source has them, don't add newlines if source doesn't, forbid adjusting newline positions
  - Used bold format to increase LLM attention
  - Rule numbering adjusted: original 8th rule becomes 8th, subsequent rules shifted accordingly
  - Note: This rule was later removed on 2026-06-13 as part of centralizing newline cleanup at extraction stage.


## 2026-06-11

- Fixed Page 22 Acknowledgments cross-paragraph merge causing out-of-order text — added paragraph boundary detection to LLM prompts:
  - Added **Example F: Paragraph Boundary** few-shot example in `modules/semantic_analyzer.py` `_generate_batch_semantic_analysis_prompt` — showing two complete body paragraphs should not merge (previous ends with period + next starts with new sentence + topic shift)
  - Strengthened "[Further Judgment]" criteria — added explicit paragraph boundary detection rules: ① previous block ends with terminating punctuation; ② next block starts with new sentence marker; ③ next block introduces new topic or subject
  - `_generate_semantic_analysis_prompt` (single-pair version) synchronized with same paragraph boundary example and rules
- Removed "segment length balance adjustment" step from `split_translated_result` — this step broke text order:
  - Removed L660-709 code block from `utils/text_processing.py`
  - Root cause: this logic extracted text from last block's tail and distributed evenly to previous blocks, causing friend acknowledgment list to be inserted at paragraph beginning, directly breaking text order
- Optimized LLM prompts to be language-agnostic — support all source languages (not just English):
  - Signature line/list item feature descriptions changed to language-agnostic (no longer depend on specific symbols like `—`/`•`/`-`)
  - Few-shot example reasoning changed to generic descriptions (no longer reference English-specific concepts like "uppercase/lowercase letters")
  - [Further Judgment] rules changed to language-agnostic ("independent new subject/topic" replaces "uppercase letter start")
- Refactored semantic merge to sequential block list mode — eliminate duplicate text and enable context-aware judgment:
  - `modules/semantic_analyzer.py` `_generate_batch_semantic_analysis_prompt` signature changed from `(text_pairs, source_lang)` to `(blocks, source_lang)`, prompt completely rewritten:
    - Input changed from paired text pairs (previous pair's block2 = next pair's block1, sliding window overlap) to sequential block listing (block1, block2, ..., blockN), each block appears only once
    - Output requirement changed to N-1 merge decisions (merge array length = block count - 1)
    - Added "Context-Aware Guidance" section: instruct LLM to reference semantic roles and content of blocks 1 through i-1 when judging block i and block i+1
  - `modules/semantic_analyzer.py` `batch_analyze_semantic_relationship` signature changed from `(text_pairs, source_lang)` to `(blocks, source_lang)`, returns `len(blocks)-1` decisions
  - `modules/aiping_semantic_analyzer.py` synchronized with new interface signature
  - `utils/text_processing.py` `parallel_batch_analyze` implemented overlap-1-block batching strategy:
    - Batch 0 takes blocks[0:batch_size], batch k takes blocks[prev_last_idx:prev_last_idx+batch_size] (includes previous batch's last 1 block as context overlap)
    - N blocks output N-1 decisions, concatenate directly without discarding
    - Verified: 25 blocks in 3 batches → 9+9+6=24=25-1 ✓
  - `utils/text_processing.py` `merge_semantic_blocks_with_llm_two_phase` builds `block_texts` list instead of `text_pairs`
  - `utils/text_processing.py` `merge_semantic_blocks_with_llm` builds `batch_block_texts` list instead of `batch_text_pairs`
  - 3 test files adapted to new interface, all 25 tests passing
- Restored newline cleaning during text extraction — fixed title text containing newlines causing truncation:
  - OCR extraction: Added `TITLE_LABELS` constant in `modules/ocr/paddle_extractor.py`, cleaning title newlines in `_build_text_from_textlines` method
  - Non-OCR extraction: Added `update_text_block_style` handling in `modules/pdf_extractor.py`
  - Cleaning strategy: Replace `\n` with space, clean extra spaces
  - Impact: Improved title text rendering quality, avoided excessive truncation
- Related files:
  - `modules/semantic_analyzer.py`
  - `modules/aiping_semantic_analyzer.py`
  - `modules/ocr/paddle_extractor.py`
  - `modules/pdf_extractor.py`
  - `utils/text_processing.py`
  - `tests/test_batch_semantic_analysis.py`
  - `tests/test_semantic_analyzer.py`
  - `tests/test_two_phase_merge.py`

## 2026-06-10

- Fixed text blocks with different alignments being incorrectly merged, causing out-of-order translation output (signature/title/list-item boundary recognition):
  - Added `alignment` attribute to `TextBlock` model (`models/text_block.py`): 0=left, 1=center, 2=right, with serialization support
  - Added `detect_text_block_alignment()` function in `modules/extractors/coordinate_utils.py`: infers text block alignment from bbox position relative to page width, left/right alignment checked before center (15% threshold)
  - `modules/pdf_extractor.py` non-OCR path calls `detect_text_block_alignment` to set TextBlock.alignment during extraction
  - `modules/ocr/paddle_extractor.py` OCR path also sets TextBlock.alignment during extraction
  - All three merge functions in `utils/text_processing.py` (`merge_semantic_blocks`, `merge_semantic_blocks_with_llm`, `merge_semantic_blocks_with_llm_two_phase`) added alignment check: blocks with different alignments are not merged
  - `modules/pdf_generator.py` uses TextBlock.alignment instead of hardcoded alignment=0 for rendering
  - Fixed alignment detection priority: changed from "center → right → left" to "left → right → center", fixing issue where symmetric layouts had all text misidentified as centered
- Rewrote LLM semantic analysis prompts — enhanced boundary recognition for signatures/titles/list items:
  - Completely rewrote `_generate_batch_semantic_analysis_prompt` in `modules/semantic_analyzer.py`:
    - Two-step analysis: first identify semantic role (body/title/signature/list_item/quote_body), then decide merge based on decision matrix
    - Defined 5 semantic roles with feature descriptions and judgment criteria
    - Added merge decision matrix: signature → any role = direct false; title → body/list_item = direct false, etc.
    - Added 5 few-shot boundary examples: signature boundary (A), same-quote continuation (B), between list items (C), list continuation (D), title boundary (E)
  - Synchronized rewrite of `_generate_semantic_analysis_prompt` (single-pair version) with same two-step approach and examples
  - `AipingSemanticAnalyzer` inherits base class prompt methods; changes take effect automatically without modification
  - Verified: Page 3 Praise review page LLM decisions improved from [true×7] to [false,false,false,false,true,false,false]; signatures no longer cross-quote merged with next quote body
- Fixed split block bbox x1 overflow:
  - `services/translation_service.py` added x1 upper bound protection: `min(original_bbox[0] + max_width, original_bbox[2])`
  - Root cause: using uniform `x0 + max_width` for x1 calculation caused blocks with larger x0 to exceed original bbox and page width (e.g., Madhav quote last sentence x0=192.24 resulted in x1=537.00)
- Preserve original newlines and whitespace:
  - Removed `text.strip()` call in `models/text_block.py`, storing original text format as-is
- Related files:
  - `models/text_block.py`
  - `modules/extractors/coordinate_utils.py`
  - `modules/pdf_extractor.py`
  - `modules/ocr/paddle_extractor.py`
  - `modules/pdf_generator.py`
  - `modules/semantic_analyzer.py`
  - `services/translation_service.py`
  - `utils/text_processing.py`

## 2026-06-09 (continued)

- Fixed Roman numeral page numbers not recognized as footers, causing cross-page text merging errors:
  - Added `roman_to_int()` function in `text_analyzer.py`: converts Roman numerals (e.g., xv, xii) to integers
  - Added `ROMAN_NUMERAL_PATTERN` regex in `text_analyzer.py`: matches standalone Roman numerals
  - Added Roman numeral page number detection in `identify_page_numbers()`: detects standalone Roman numerals in top/bottom 15% area with font size < 10.0, supports sequential increment pattern and value matching
  - Added 14 unit tests (`test_text_analyzer.py`), all 35 tests passing
- Fixed merged block split bbox height too large causing text overflow and paragraph occlusion:
  - `translation_service.py` split block bbox height now uses each block's own `original_bbox[3]`, width still uses `max_width`
  - No longer uses `max_height` to expand split block height, avoiding downward expansion occluding the next block
- Fixed CJK font line height larger than Latin font causing translated text to overflow bbox:
  - `pdf_generator.py` added original text line height ratio calculation: `lineheight = bbox_height / (font_size × estimated_lines)`, minimum 1.0, default 1.2
  - All `insert_textbox()` calls now include `lineheight` parameter, making translated text line height consistent with original
  - Table rendering uses `lineheight=1.2` default value
- Fixed PDF generator first render using enlarged font causing text overflow:
  - `pdf_generator.py` first attempt uses original font size, progressively shrinks on overflow (1.0x → 0.9x → 0.8x → 0.7x)
- Fixed merged block split equal distribution causing second block to be empty and translated text loss:
  - Added `_get_original_text_len()` helper function in `text_processing.py`
  - `split_translated_result()` allocation strategy changed from equal distribution to proportional by original text length
  - Added protection: non-last block's `actual_end` does not exceed `translation_len - min_characters_per_block × remaining_blocks`
- Related files:
  - `modules/extractors/text_analyzer.py`
  - `modules/pdf_generator.py`
  - `services/translation_service.py`
  - `utils/text_processing.py`
  - `tests/test_text_analyzer.py`

## 2026-06-09

- Word table size matching original PDF:
  - Rewrote `docx_generator.py` `_add_table()`: uses `PdfTable.col_widths`/`row_heights`/`bbox` for table sizing instead of uniform splitting
  - Added `_resolve_col_widths()` and `_resolve_row_heights()` helper methods with PDF point to Word unit conversion (1pt=12700EMU, 1in=1440twips)
  - Merged cell width/height distributed equally across spanned columns/rows
  - Table layout set to `tblLayout=fixed` with precise column widths via `tblGrid`/`gridCol`
- PDF and Word table alignment matching original PDF:
  - Added `alignment` parameter to `PdfCell` (0=left, 1=center, 2=right) and `PdfTable` (default 1=center)
  - Added `extract_cell_alignment()` in `coordinate_utils.py`: infers alignment from character bbox position relative to cell bbox (center offset <15% → centered, left offset <10% → left-aligned, right offset <10% → right-aligned)
  - Added `extract_table_alignment()` in `coordinate_utils.py`: infers table-level alignment from table bbox position relative to page width
  - `table_processor.py` computes text bbox from character-level bboxes per cell and calls `extract_cell_alignment` to set cell alignment
  - `paddle_extractor.py` OCR mode alignment extraction: uses textline bbox center offset to infer cell alignment
  - `pdf_generator.py` uses `cell.alignment` instead of hardcoded `align=1`
  - `docx_generator.py` uses `table.alignment` for table-level alignment and `cell.alignment` for cell paragraph alignment
  - PyMuPDF has no native alignment attribute; alignment is fully inferred from character positions
- Related files:
  - `models/extraction.py`
  - `modules/docx_generator.py`
  - `modules/extractors/coordinate_utils.py`
  - `modules/extractors/table_processor.py`
  - `modules/ocr/paddle_extractor.py`
  - `modules/pdf_generator.py`

- Fixed `Rect.intersect()` in-place mutation causing table text overlap detection failure:
  - PyMuPDF's `Rect.intersect()` mutates the caller rectangle, causing all cumulative overlap area calculations in `_extract_text_blocks` to be incorrect
  - Fix: Changed 5 occurrences of `.intersect()` to `&` operator across 3 files (returns new rect, doesn't mutate original)
  - Added cumulative overlap area detection: text block marked as table text only when total overlap with all cells exceeds 50%
  - Added empty list fallback: when `table_cell_bboxes` is empty, fall back to table overall bbox detection
  - Added `table_bbox` parameter to filter out-of-table characters: `extract_table_cells_by_bbox` filters characters whose center is outside table bbox
- Word merged cell support:
  - `docx_generator.py` `_add_table()` added merge traversal: calls `cell.merge()` for cells with `row_span > 1` or `col_span > 1`
  - Skips `None` positions (cells covered by merge)
  - Merged cell font size scaled by span
- Markdown merged cells (not yet enabled):
  - Discovered `_format_with_layout_model` sends HTML tables to LLM for reformatting, LLM converts HTML back to pipe format losing `colspan`/`rowspan`
  - Needs placeholder protection mechanism (similar to formula protection) before enabling
- Fixed `\$` invalid escape sequence SyntaxWarning in `markdown_generator.py`
- Added `tests/test_rect_intersect_fix.py`: 13 test cases covering Rect behavior, overlap detection, character filtering
- Related files:
  - `modules/pdf_extractor.py`
  - `modules/extractors/table_processor.py`
  - `modules/extractors/style_analyzer.py`
  - `modules/docx_generator.py`
  - `modules/markdown_generator.py`
  - `tests/test_rect_intersect_fix.py`

## 2026-06-08

- Merged cell rendering optimization — fix text truncation and line separation issues:
  - Added `row_span` and `col_span` fields to `PdfCell` (default 1), with `from_dict`/`to_dict` serialization support
  - OCR mode: `_TableHtmlParser` parses `rowspan`/`colspan` attributes, `_expand_html_table` expands to full 2D matrix (start position PdfCell, merged positions None)
  - PyMuPDF mode: Added `compute_span_from_none_positions()` function to infer row_span/col_span from None distribution in bbox_matrix
  - PDF generation: Merged cells use full spanning bbox for text rendering, grid lines drawn by visible segments (skipping merged cell interiors)
  - Column width calculation: Added proportional scaling to ensure `sum(col_widths) == table_width`, fixing horizontal lines exceeding table boundary
- Merged cell occlusion logic refinement:
  - Horizontal line occlusion: only exclude top/bottom borders of col_span>1 cells (multi-column borders should be fully drawn)
  - Vertical line occlusion: only exclude left/right borders of row_span>1 cells (multi-row borders should be fully drawn)
  - row_span interior horizontal lines and col_span interior vertical lines are correctly occluded
- Code review optimizations:
  - Simplified `compute_span_from_none_positions` step 3 validation logic, removed conflicting `covered_by_col_span` checks
  - Extracted `_get_cell_span()` helper function, replacing 9 duplicate `getattr(cell, 'row_span', 1)` calls
  - Downgraded 7 merged cell debug logs from `logger.info` to `logger.debug`
- Related files:
  - `models/extraction.py`
  - `modules/extractors/coordinate_utils.py`
  - `modules/extractors/table_processor.py`
  - `modules/ocr/paddle_extractor.py`
  - `modules/pdf_generator.py`
  - `services/translation_service.py`

## 2026-06-07

- Non-OCR mode table precise restoration — use PyMuPDF real cell bbox instead of uniform splitting:
  - Added `_build_bbox_matrix()` function to convert `rows_data` from `extract_table_cells_by_bbox` into row×col bbox matrix
  - Added `calculate_row_heights_from_bboxes()` function to calculate row heights from real bboxes (max y1-y0 per row)
  - Added `calculate_col_widths_from_bboxes()` function to calculate column widths from real bboxes (merged cells distributed equally across spanned columns)
  - Modified `extract_table_cells_by_bbox` to return `rows_data` (real bbox matrix) as third return value
  - Modified `extract_tables_by_pymupdf` to prefer real bbox, with uniform splitting as fallback
  - Modified `extract_tables_by_pymupdf` to prefer row/col size calculation from real bboxes
- Fixed table row translation separator loss causing cell content duplication:
  - Added rule 17 to `translator.py` system prompt: preserve "|||" separators, translate each segment independently without merging
  - Added fallback in `translate_table_row` for separator count mismatch: translate each cell individually
- OCR mode table grid layout refactoring:
  - Refactored `paddle_extractor.py` `_compute_table_grid()` to use column boundary clustering instead of uniform splitting
  - Unified cell heights within same row and cell widths within same column, fixing OCR mode table misalignment
  - Added `_cluster_1d()` 1D clustering function for row/column boundary detection
- Fixed tests to adapt to `extract_tables` return value change (3-tuple to 4-tuple)
- Related files:
  - `modules/extractors/coordinate_utils.py`
  - `modules/extractors/table_processor.py`
  - `modules/ocr/paddle_extractor.py`
  - `modules/translator.py`
  - `services/translation_service.py`
  - `tests/test_pdf_extractor.py`

## 2026-06-06

- Fixed date-style footer not recognized, causing cross-page incorrect merge:
  - Fixed `text_analyzer.py` `_add_similar_blocks()` short text similarity threshold from 1.0 (exact match) to 0.8
  - Previous threshold was too strict, preventing date-style footers like "2025年2月 8" and "2025年2月 9" from being detected
  - Simplified tiered thresholds to a single 0.8 threshold, covering date-style footers (LCS similarity ≈ 88.9%)
- Fixed text box exceeding original width and page width:
  - Fixed `pdf_generator.py` overflow retry logic: clamped right/bottom edges to page boundaries (`min(x0+width, page.width)`)
  - Reduced `paddle_extractor.py` `_compute_tight_bbox()` width tolerance from 30% to 10%
  - Added page width clamping to tight bbox, preventing OCR detection noise from pushing bbox beyond page
- Fixed tight bbox height being too large:
  - Added height 10% tolerance clamping in `_compute_tight_bbox()` (symmetric with width), preventing line spacing from inflating bbox height
  - Added `_estimate_font_size_from_textlines()` helper method, using average textline height for font_size estimation
  - Fixed font_size estimation in 5 non-TEXT_LABELS paths (formula, figure_caption, else, supplement, formula_res_list) from `bbox_height * 0.75` to textline average height * 0.75
- Related files:
  - `modules/pdf_generator.py`
  - `modules/ocr/paddle_extractor.py`

## 2026-06-05

- Fixed OCR text extraction missing on page 28 (title "Aim" and paragraph not recognized):
  - Fixed `rec_text` → `rec_texts` typo in `paddle_extractor.py` line 599, causing all textline text to be None
  - Removed `header` from `NON_BODY_LABELS` — layout labels like `header` are now treated as body text by default; actual page headers are identified by `text_analyzer.py` based on multi-page repetition patterns
  - Fixed `_add_similar_blocks` short text false positives: short text (<20 chars) only marked as non-body when 100% identical; long-short pairs use ≥95% threshold; long-long pairs use ≥90% threshold
  - Added `processed_pixel_bboxes` to track only successfully created blocks, preventing empty-text blocks from blocking supplement capture
  - Relaxed supplement capture precondition from `len(textline_texts) > 0` to `len(textline_boxes) > 0`
  - Added `[TEXT_SKIP]` WARNING log for text extraction failures and `[OCR_WARN]` log for `rec_texts` length mismatch
- Code review optimizations:
  - Extracted supplement capture text filter logic into `_filter_uncovered_textlines` static method, reducing nesting from 5 to 3 levels
  - Added `[TEXT_SKIP]` WARNING log to `else` (unknown label) branch for consistency with TEXT_LABELS branch
  - Moved `SHORT_TEXT_THRESHOLD` from local variable to module-level constant in `text_analyzer.py`
  - Changed `rec_texts` length mismatch log tag from `[FONT_DEBUG]` to `[OCR_WARN]`
  - Cleaned up `_step1_use_formula` variable naming to `use_formula`
- Regression test fixes:
  - Fixed `test_system_profiler.py` 4 tier test failures: added `total_memory_gb` parameter matching tier thresholds
  - Added `--ignore=tests/test_simple_pdf_gen.py` to `pytest.ini` to prevent collection crash
  - Fixed PytestReturnNotNoneWarning in 6 test files: replaced `return True/False` with `assert` statements
- Related files:
  - `modules/ocr/paddle_extractor.py`
  - `modules/extractors/text_analyzer.py`
  - `tests/test_ocr_extractor.py`
  - `tests/test_system_profiler.py`
  - `tests/test_chapter_identifier_cache.py`
  - `tests/test_list_item_continuation.py`
  - `tests/test_semantic_merge_optimization.py`
  - `tests/test_table_text_in_glossary.py`
  - `tests/test_two_phase_merge.py`
  - `pytest.ini`

- Fixed inaccurate translation progress display and progress regression:
  - Reassigned phase percentage ranges: init 0-5, extraction 5-40, semantic_merge 40-50, translation 50-85, table_translation 85-92, generation 92-98, clean 98-100
  - Fixed `models/phase_config.py` integer truncation: `calculate_progress` uses `round()` instead of `//`
  - Fixed `models/task.py` progress calculation: `update_phase_progress` uses `round()` instead of `//`, `set_error` preserves current progress instead of resetting to 0
  - Fixed `services/translation_service.py` OCR progress callback logic:
    - `STEP_WEIGHTS` changed from `{1: 0.45, 1.5: 0.05, 2: 0.25, 3: 0.25}` to `{1: 0.80, 2: 0.20}`, removed non-existent steps 1.5 and 3
    - Added `_prior_weights` table, `step_start` uses cumulative weight of previous steps to prevent progress regression to 5%
    - `step_complete` advances progress to cumulative weight upper bound
    - Unified message format: step_start/step_progress/step_complete
    - Removed `message` dead code and step 1.5 skip warning handling
  - Fixed `modules/ocr/paddle_extractor.py` OCR step callbacks:
    - Defined step constants `STEP_LAYOUT_OCR`/`STEP_LAYOUT_OCR_NAME`/`STEP_IMAGE_CROP`/`STEP_IMAGE_CROP_NAME`, eliminated hardcoding
    - Step 1 name changed from "版面分析+文本OCR" to "版面分析+文本+公式+表格"
    - Added `step_start`/`step_complete` callbacks for step 2 (image cropping)
    - Added `step_name` field to `step_progress` payload
    - Removed `total_pages` from step 2 `step_start` (step 2 doesn't process by page)
  - Fixed `services/translation_service.py` translation flow progress:
    - Fixed `_complete_task` flow: generation 100% after file generation, clean 0%/100% before/after cleanup
    - `translate_tables` returns empty list directly when no tables, skipping table_translation phase
    - `generate_output_files` updates fine-grained progress by output format
    - `translate_content` passes `progress_callback` to merge functions
  - Fixed `utils/text_processing.py` merge functions to support progress callback
  - Fixed `services/glossary_service.py` glossary extraction progress: removed duplicate init setting, added pdf_extraction start progress
  - Fixed `app.py` glossary error handling to use `set_error()`
- Related files:
  - `models/phase_config.py`
  - `models/task.py`
  - `modules/ocr/paddle_extractor.py`
  - `services/translation_service.py`
  - `services/glossary_service.py`
  - `utils/text_processing.py`
  - `app.py`

- Fixed OCR formula recognition failure across all three output formats (PDF/Word/Markdown):
  - Fixed `modules/ocr/system_profiler.py` memory tier logic: `_determine_tier` now uses physical memory (`total_memory_gb`) instead of available memory, preventing 16GB machines from being incorrectly downgraded to `minimal` tier
  - Adjusted `system_profiler.py` DPI tier parameters: `minimal` from 100 to 120, `medium` from 120 to 150, `unlimited` from 150 to 200, improving OCR recognition quality on low-memory machines
  - Adjusted `system_profiler.py` inference parameters: `text_det_limit_side_len` for `minimal` and `low` tiers raised from 720 to 960, ensuring sufficient formula detection resolution
  - Fixed `system_profiler.py` log format: tier log now shows total memory before available memory for clarity
  - Fixed `modules/ocr/paddle_extractor.py` misleading log: removed the logic that forced `text_det_limit_side_len=960` when `use_formula=True`, log now accurately reflects actual parameters
  - Improved `modules/ocr/paddle_extractor.py`: added `header` label to `NON_BODY_LABELS` to prevent headers from being translated as body text
  - Optimized `modules/ocr/ocr_worker.py` parameter degradation strategy: degradation factor from 0.7 to 0.8, DPI step from -30 to -20, gentler degradation to avoid excessive quality loss
  - Optimized `modules/ocr/ocr_worker.py`: auto-skip table and formula recognition during retry degradation (`skip_table`/`skip_formula`), prioritizing basic text extraction success
  - Fixed `utils/text_processing.py` text block merge height calculation: use `max()` for maximum height instead of direct overwrite, preventing incorrect merged block height
  - Fixed `tests/test_semantic_merge_extended.py` test assertions: corrected `block_text` property access, removed redundant test cases
  - Fixed `tests/test_translation_service.py` tests: adapted to `extract()` return value change (returns tuple), removed outdated comment assertions
- Related files:
  - `modules/ocr/system_profiler.py`
  - `modules/ocr/paddle_extractor.py`
  - `modules/ocr/ocr_worker.py`
  - `utils/text_processing.py`
  - `tests/test_semantic_merge_extended.py`
  - `tests/test_translation_service.py`

## 2026-06-04

- Implemented OCR extraction engine improvements and code review fixes:
  - Fixed `_logging` undefined NameError in `modules/ocr/ocr_worker.py` causing OCR subprocess crash (changed to `logging`)
  - Added `tests/test_ocr_worker.py`, covering OCR worker exception types, heartbeat, parameter degradation, subprocess retry logic
  - Added `tests/test_system_profiler.py`, covering system resource detection, 5 memory tier parameter calculation, high load parameter reduction
  - Added `tests/test_omml_constants.py`, testing OMML constant definitions
  - Added `tests/test_table_grid.py`, testing table grid layout calculation
  - Updated `tests/test_ocr_extractor.py`, covering factory creation, extraction, tables, GPU fallback scenarios
  - Added `modules/ocr/system_profiler.py`, implementing system resource adaptive parameter calculation
  - Refactored `modules/ocr/ocr_worker.py`, enhanced subprocess management, heartbeat monitoring, dynamic timeout and parameter degradation retry
  - Refactored `modules/ocr/paddle_extractor.py`, enhanced LaTeX cleaning, figure_caption text extraction, table HTML extraction fix
  - Added `install_paddle.sh`, auto-detect OS and CUDA version for PaddlePaddle installation
  - Updated `README.md` and `README.zh.md`, added OCR installation and usage instructions
  - Updated `SKILL.md`, added OCR-related skill documentation
  - Modified `modules/pdf_extractor.py`, enhanced OCR mode integration
  - Modified `modules/pdf_generator.py`, optimized PDF generation and resource release
  - Modified `modules/docx_generator.py`, enhanced Word document generation
  - Modified `modules/markdown_generator.py`, optimized Markdown generation
  - Modified `services/translation_service.py`, enhanced translation service and OCR integration
  - Modified `utils/text_processing.py`, fixed text block merge height calculation bug
  - Modified `config.py`, added OCR-related configuration parameters
  - Updated `requirements.txt`, added OCR dependencies
- Related files:
  - `modules/ocr/ocr_worker.py`
  - `modules/ocr/paddle_extractor.py`
  - `modules/ocr/system_profiler.py`
  - `modules/pdf_extractor.py`
  - `modules/pdf_generator.py`
  - `modules/docx_generator.py`
  - `modules/markdown_generator.py`
  - `services/translation_service.py`
  - `utils/text_processing.py`
  - `config.py`
  - `install_paddle.sh`
  - `tests/test_ocr_worker.py`
  - `tests/test_system_profiler.py`
  - `tests/test_ocr_extractor.py`
  - `tests/test_omml_constants.py`
  - `tests/test_table_grid.py`

## 2026-05-29

- Uploaded OCR requirement documents and PRP files:
  - Added `docs/OCR-requiremnt.md`, defining three-phase OCR feature planning
  - Added `.claude/PRPs/plans/pdf-ocr-extraction.plan.md`, OCR extraction implementation plan
  - Added `.claude/PRPs/prds/pdf-ocr-extraction.prd.md`, OCR extraction product requirements document
  - Added `plans/ocr-timeout-optimization.md`, OCR timeout optimization plan
  - Added `tests/test_ocr_extractor.py`, OCR extractor test cases
- Related files:
  - `docs/OCR-requiremnt.md`
  - `.claude/PRPs/plans/pdf-ocr-extraction.plan.md`
  - `.claude/PRPs/prds/pdf-ocr-extraction.prd.md`
  - `plans/ocr-timeout-optimization.md`
  - `tests/test_ocr_extractor.py`

## 2026-05-29

- Implemented OCR mode improvements, security fixes and code quality enhancements:
  - Created `modules/ocr/` package with OCR engine architecture:
    - `base.py`: Defined `OcrExtractor` abstract base class, unified OCR engine interface
    - `factory.py`: Factory function `create_ocr_extractor()`, supporting engine extension
    - `__init__.py`: Module entry point, exporting core classes and exceptions
  - Implemented `modules/ocr/paddle_extractor.py` PaddleOCR extractor core:
    - Step-by-step loading strategy based on PP-StructureV3, avoiding 2.5GB+ memory overflow
    - Support for text block extraction, table recognition, formula recognition (LaTeX extraction and cleaning), image region cropping
    - GPU auto-detection and CPU fallback mechanism
    - Memory check: verify available memory before creating pipeline
    - Logger recovery: auto-restore root logger configuration after PPStructureV3 construction
    - Font size estimation: three-tier strategy fixing oversized estimation for multi-line text blocks
    - Precise bounding boxes: using textline-level bbox for tight bbox calculation
    - Table grid layout calculation: computing unified grid bbox based on textline data
  - Implemented `modules/ocr/ocr_worker.py` OCR subprocess worker:
    - Independent subprocess (spawn mode) to prevent main process crashes
    - Heartbeat monitoring and progress stall detection
    - Dynamic timeout extension and parameter degradation retry
  - Implemented `modules/ocr/system_profiler.py` system resource adaptive parameters:
    - 5 memory tiers (minimal/low/medium/high/unlimited) with auto parameter calculation
    - Automatic parameter reduction under high load
  - Extended data models in `models/extraction.py`:
    - Added `from_dict()`/`to_dict()` serialization methods for inter-process data transfer
    - `PdfTable` added `row_heights` and `col_widths` fields
  - Security fixes:
    - Removed hardcoded `SECRET_KEY` default value in `config.py`, enforcing environment variable configuration
    - Safe `DEBUG` default value handling
    - Download filename regex validation, preventing path traversal attacks
    - Page range input length limit (1000 characters), preventing DoS
  - Code quality improvements:
    - Translation API exception fallback returns original text instead of empty string
    - Font size estimation fix (multi-line block 120pt estimated as 9pt instead of 90pt)
    - PDF generator resource release protection (try/finally ensuring close())
    - numpy array truth value check fix
  - Added `install_paddle.sh` PaddlePaddle installation script
  - Added `tests/test_code_review_fixes.py` code review fix tests
  - Modified `app.py`, added OCR mode support
  - Modified `cli.py` and `cli/translate_command.py`, added OCR command line options
  - Modified `config.py`, added numerous OCR-related configuration parameters
  - Modified `modules/pdf_extractor.py`, integrated OCR extraction
  - Modified `modules/pdf_generator.py`, optimized PDF generation
  - Modified `services/translation_service.py`, integrated OCR translation service
  - Modified `templates/index.html`, added OCR UI elements
  - Updated `requirements.txt`, added OCR dependencies
- Related files:
  - `modules/ocr/base.py`
  - `modules/ocr/factory.py`
  - `modules/ocr/__init__.py`
  - `modules/ocr/paddle_extractor.py`
  - `modules/ocr/ocr_worker.py`
  - `modules/ocr/system_profiler.py`
  - `models/extraction.py`
  - `models/text_block.py`
  - `config.py`
  - `app.py`
  - `cli.py`
  - `cli/translate_command.py`
  - `modules/pdf_extractor.py`
  - `modules/pdf_generator.py`
  - `services/translation_service.py`
  - `templates/index.html`
  - `install_paddle.sh`
  - `tests/test_code_review_fixes.py`
  - `requirements.txt`

## 2026-03-30

- Added command line support:
  - Added `cli.py` command line entry file
  - Added `cli/` directory with command processing modules
  - Added `setup.py` installation configuration
  - Added `tests/test_cli.py` command line tests
  - Added `tests/test_output_filename.py` output filename tests
  - Added `SKILL.md` skill documentation
  - Added `.trae/skills/` skill directory
  - Added `.trae/specs/` specification directory
  - Added `.trae/documents/` related documents
- Fixed output directory and image extraction permission issues:
  - Modified `modules/pdf_extractor.py` to add `temp_images_dir` parameter
  - Modified `services/translation_service.py` to add `output_path` and `tmp_dir` parameter support
  - Modified `services/glossary_service.py` to add `tmp_dir` parameter support
  - Updated `README.md` and `README.zh.md` to add output directory and temporary file instructions
  - Updated `.trae/documents/ai_dev_progress.md` to record development progress
- Added skill-related documentation:
  - Added skill integration section in `README.md` and `README.zh.md`
  - Added API key configuration instructions
  - Documented smart defaults, optimized output, intelligent suffix handling, and error handling features
- Related files:
  - `cli.py`
  - `cli/` directory
  - `setup.py`
  - `tests/test_cli.py`
  - `tests/test_output_filename.py`
  - `SKILL.md`
  - `modules/pdf_extractor.py`
  - `services/translation_service.py`
  - `services/glossary_service.py`
  - `README.md`
  - `README.zh.md`

## 2026-03-19

- Added GitHub Actions sync workflow:
  - Created `.github/workflows/sync-gitee-to-github_ssh.yml` file to implement syncing from Gitee to GitHub using SSH keys
  - Configured daily auto-sync at UTC 11:00 (Beijing time 19:00)
  - Supported manual trigger for syncing
  - Implemented SSH key configuration, Git user setup, repository cloning and syncing logic
  - Added retry mechanism to ensure stable and reliable sync process
  - Force pushed all branches and tags to ensure complete consistency between Gitee and GitHub repositories
- Related files:
  - `.github/workflows/sync-gitee-to-github_ssh.yml`

## 2026-03-16

- Implemented translation progress system refactoring:
  - Created `models/phase_config.py` to define translation stage configurations including extraction, translation, merging, generation, and cleanup stages
  - Modified `models/task.py` to add `CopyableMixin` inheritance for deep copy support
  - Added `set_task_type()` method to support translation and glossary extraction task types
  - Added `update_phase_progress()` method for fine-grained progress tracking
  - Added task start and end time recording
  - Upgraded `threading.Lock()` to `threading.RLock()` for recursive lock support
- Optimized translation service progress updates:
  - Modified `services/translation_service.py` to use `update_phase_progress()` instead of `update_progress()`
  - Implemented fine-grained progress updates for each stage (extraction, translation, merging, generation, cleanup)
  - Added progress update functionality for page copying
  - Optimized progress calculation for page processing
- Implemented two-phase semantic block merging:
  - Created `merge_semantic_blocks_with_llm_two_phase()` function in `utils/text_processing.py`
  - Phase 1: Semantic merging based on sentence-level judgment
  - Phase 2: Semantic merging based on paragraph-level judgment
  - Added `_check_paragraph_continuation()` function to determine paragraph continuation
  - Optimized merging logic calls in translation service
- Optimized text block merging algorithm:
  - Modified `merge_semantic_blocks()` function in `utils/text_processing.py`
  - Improved sentence continuation detection to support more punctuation types (lowercase letters, punctuation marks)
  - Added paragraph continuation detection to ensure blocks in the same paragraph are merged correctly
  - Optimized vertical distance checking and chapter information processing
- Added new data models:
  - Created `models/copyable.py` with `CopyableMixin` abstract class for deep copy support
  - Created `models/phase_config.py` to define translation stage configuration constants
- Optimized glossary extraction service:
  - Modified `services/glossary_service.py` to support progress tracking for glossary extraction
  - Improved glossary extraction logic to enhance accuracy
- Fixed test cases:
  - Updated `tests/test_semantic_analyzer.py` to fix merged block count assertions
  - Updated `tests/test_title_body_separation.py` to fix title-body separation test assertions
  - Updated `tests/test_pdf_page_translation.py` to fix mock verification issues
- Created new test cases:
  - Created `tests/test_two_phase_merge.py` to test two-phase merging functionality
  - Created `tests/test_split_sentence.py` to test sentence splitting functionality
  - Created `tests/test_list_detection.py` to test list detection functionality
- Related files:
  - `models/task.py`
  - `models/phase_config.py`
  - `models/copyable.py`
  - `services/translation_service.py`
  - `services/glossary_service.py`
  - `utils/text_processing.py`
  - `modules/markdown_generator.py`
  - `modules/semantic_analyzer.py`
  - `tests/test_two_phase_merge.py`
  - `tests/test_split_sentence.py`
  - `tests/test_list_detection.py`

## 2026-03-13

- Fixed PDF chapter title position identification issue:
  - Improved `_find_title_position` method in `modules/chapter_identifier.py`
  - Implemented exact match, high similarity match, substring match, and cross-block match strategies
  - Used `difflib.SequenceMatcher` to calculate text similarity
  - Added comprehensive scoring system to select best match
  - Supported identifying titles spanning multiple consecutive text blocks
  - Resolved issue where "Introduction to Agents and Agent architectures" was incorrectly identified as "Agents and Agents" chapter
- Created test cases:
  - Created `tests/test_title_position_fix.py` with 6 complete test cases
  - Tested exact match, avoiding substring false matches, cross-block match, high similarity match scenarios
- Test verification:
  - All 6 new test cases passed
  - All 12 existing related tests passed
  - Verified actual PDF file processing works correctly
- Related files:
  - `modules/chapter_identifier.py`
  - `tests/test_title_position_fix.py`

## 2026-03-13

- Optimized translation progress bar prompts:
  - Added initial stage progress prompts (0%, 5%, 10%) in `services/translation_service.py`
  - Refined semantic merging stage progress prompts (45%, 47%, 50%)
  - Optimized output file generation stage progress prompts (80%, 90%, 95%, 100%)
  - Ensured smooth progress value transitions to eliminate user feeling of "stuck"
- Enhanced table translation logging:
  - Added detailed logging in table translation process
  - Recorded table processing, cell translation, and result storage details
  - Improved system debuggability and problem location capability
- Implemented smart default chapter naming:
  - Modified `chapter_identifier.py` to add smart naming using the first text block on a page as default chapter name
  - Added `use_smart_naming` and `max_title_length` configuration parameters
  - Implemented `_get_first_text_block()` method to get the first text block on a page
  - Implemented `_truncate_title()` method to truncate long titles
  - Added fallback logic: use filename and page number as title when page has no text blocks
- Enhanced chapter identification:
  - Improved `_find_title_position()` method to add exact match, high similarity match, substring match, and cross-block match
  - Added detailed logging to improve debugging efficiency
  - Enhanced chapter association logging for text blocks, tables, and images
- UI text optimization:
  - Changed "按章节拆分Markdown" to "按章节翻译Markdown"
  - Optimized hint text to "启用后按章节拆分翻译并生成多个Markdown文件"
  - Modified related text in `templates/index.html`, `static/js/main.js`, and `services/translation_service.py`
- Created test cases:
  - Created `tests/test_default_chapter.py` with 14 complete test cases
  - Tested default configuration, custom configuration, no-chapter page detection, smart naming, fixed naming, empty page handling, long title truncation
  - Used Mock technology to simulate PDF text extraction for test reliability
- Regression testing:
  - All 14 smart default chapter naming test cases passed
  - Full test suite of 185 test cases all passed
- Related files:
  - `services/translation_service.py`
  - `modules/chapter_identifier.py`
  - `templates/index.html`
  - `static/js/main.js`
  - `tests/test_default_chapter.py`

## 2026-03-13

- Implemented PyMuPDF table extraction:
  - Added `extract_tables_by_pymupdf` function in `table_processor.py`
  - Used PyMuPDF's `find_tables()` method for table extraction
  - Maintained same parameter and return value format as `extract_tables_by_camelot`
  - Fixed bbox type judgment issue (tuple or Rect object)
  - Implemented table bbox calculation, cell information construction, and table structure analysis
- Integrated into PdfExtractor:
  - Added `table_extractor` parameter to support selecting Camelot or PyMuPDF
  - Default to PyMuPDF for table extraction
  - Exported new function in `__init__.py`
- UI text optimization:
  - Changed "按章节拆分Markdown" to "按章节翻译Markdown"
  - Optimized hint text to "启用后按章节拆分翻译并生成多个Markdown文件"
  - Modified related text in `index.html`, `main.js`, and `translation_service.py`
- Enhanced logging:
  - Added detailed logs in table translation process including table processing, cell translation, and result storage
  - Added debug logs in table drawing process including table structure, cell content, and translated text status
  - Changed log level from DEBUG to INFO for better readability
- Related files:
  - `modules/extractors/table_processor.py`
  - `modules/extractors/__init__.py`
  - `modules/pdf_extractor.py`
  - `modules/pdf_generator.py`
  - `services/translation_service.py`
  - `templates/index.html`
  - `static/js/main.js`
  - `utils/logging_config.py`

## 2026-03-12

- Implemented semantic block merging optimization:
  - Optimized `merge_semantic_blocks` function to add vertical distance check (threshold: 10 units)
  - Improved sentence continuation judgment logic to support Chinese and English text
  - Added chapter information processing to ensure text blocks in the same chapter are merged correctly
  - Fixed `merge_semantic_blocks_with_llm` function to add chapter information support
  - Adjusted batch processing size to 10 for better performance
- Implemented Markdown generation optimization:
  - Optimized chapter content organization using merged blocks instead of original text blocks
  - Implemented parallel chapter Markdown generation for faster processing
  - Improved result object to add chapter-level success/failure status and warning messages
  - Fixed chapter index generation logic
- Fixed function parameter names:
  - Renamed `chapter_split` parameter to `extract_chapter` for better code readability
  - Updated related function calls to ensure correct parameter passing
- Regression testing:
  - Executed full test suite to verify code changes don't break existing functionality
  - Fixed test cases to ensure all tests pass
- Related files:
  - `utils/text_processing.py`
  - `modules/markdown_generator.py`
  - `modules/pdf_extractor.py`
  - `services/translation_service.py`
  - `tests/test_title_body_separation.py`

## 2026-03-11

- Implemented chapter Markdown generation optimization:
  - Fixed chapter mapping logic to ensure all page numbers correctly associate with corresponding chapters
  - Optimized chapter content organization logic to ensure chapter files contain complete text, images, and table content
  - Simplified chapter content processing logic for better maintainability
  - Added detailed logging for debugging and issue tracking
- Fixed test cases:
  - Fixed parameter name error in `test_same_language_optimization.py`, changed `output_filename` to `filename`
  - Ensured all test cases run correctly
- Regression testing:
  - Executed full test suite to verify code changes don't break existing functionality
  - Ensured all test cases pass for better code quality

## 2026-03-06

- Implemented glossary file operations:
  - Added "Load Glossary File" and "Save Glossary to File" buttons in web interface to support importing glossaries from local files and exporting current glossary to local files
  - Implemented file loading for .txt glossary files
  - Implemented file saving to export glossary content as text file
  - Added error handling and user feedback for smooth operation
- Frontend UI optimization:
  - Reduced button height for better appearance
  - Set "Use LLM for semantic judgment" option to checked by default for better translation quality
  - Optimized glossary title and button layout for cleaner interface
- Glossary extraction service improvements:
  - Supported extracting table text from PDFs for more complete glossary extraction
  - Supported specifying page ranges for glossary extraction for better efficiency
  - Optimized extraction logic to ensure correct glossary format
- Translation service improvements:
  - Added progress updates and page processing status so users can see translation process
  - Optimized multi-threaded translation logic for better efficiency
  - Enhanced error handling and exception catching for better stability
- Testing and optimization:
  - Created `tests/test_glossary_file_operations.py` with test cases for glossary file operations
  - Executed full regression testing to ensure code changes don't break existing functionality
  - All test cases passed ensuring functionality works correctly

## 2026-03-05

- Implemented automatic glossary extraction:
  - Created `modules/glossary_extractor.py` with abstract base class and concrete implementation for glossary extraction
  - Supported glossary extraction for aiping and Silicon Flow platforms
  - Implemented `services/glossary_service.py` to provide glossary extraction from PDFs
  - Added "Extract Glossary" button in web interface to automatically extract glossary from uploaded PDFs
  - Implemented glossary extraction progress display so users can see extraction process and results
  - Optimized prompts to ensure generated glossary strictly follows "Term: Translation" format
- Frontend UI optimization:
  - Placed glossary extraction progress bar on the right side of the same row as the extract button
  - Ensured progress bar doesn't disappear after extraction so users can see results
  - Hidden cancel button after extraction for cleaner interface
  - Moved "Automatically extract glossary from uploaded PDF" text below the extract button
- Testing and optimization:
  - Created `tests/test_glossary_extractor.py` with test cases for glossary extraction
  - Executed full regression testing to ensure code changes don't break existing functionality
  - All test cases passed ensuring functionality works correctly

## 2026-02-28

- Implemented result typing:
  - Created `models/result_types.py` with `TruncationInfo`, `Result`, `OpenAIResult`, `TranslationResult`, and `MarkdownResult` classes
  - Modified `aiping_translator.py` to return `TranslationResult` objects instead of strings
  - Modified `markdown_generator.py` to return `MarkdownResult` objects instead of strings
  - Added `batch_translate` method to `AipingTranslator` class
- Optimized API calls:
  - Added `AIPING_EXTRA_BODY` configuration in `config.py` to centrally manage cost priority strategy parameters
  - Modified `aiping_translator.py`, `aiping_semantic_analyzer.py`, and `markdown_generator.py` to read `extra_body` from configuration
  - Added streaming response handling, timeout detection, token usage information capture, and truncation detection
- Implemented truncation warning:
  - Implemented `TruncationInfo` class in `models/result_types.py` for structured storage of truncation information
  - Added truncation detection logic in `services/translation_service.py` to add warnings when translation or Markdown generation is truncated
  - Implemented warning display logic in frontend `static/js/main.js` to ensure users can see truncation warnings
  - Fixed duplicate warning display issue by hiding warning area when task completes
- Other optimizations:
  - Added detailed logging for debugging and issue tracking
  - Improved code readability and maintainability

## 2026-02-27

- Implemented max_tokens property configuration:
  - Added max_tokens property to multiple modules supporting default values and external configuration
  - `markdown_generator.py`: Added max_tokens property with default value 8192
  - `aiping_semantic_analyzer.py`: Added max_tokens (default 1024) and batch_max_tokens (default 2048) properties
  - `aiping_translator.py`: Added max_tokens property with default value 8192
  - `semantic_analyzer.py`: Added max_tokens (default 1024) and batch_max_tokens (default 2048) properties
  - `silicon_flow_translator.py`: Added max_tokens property with default value 8192
  - Updated all API calls to use class properties as max token count
  - Created `test_max_tokens_property.py` test file to verify max_tokens property functionality
- Fixed image URL element loss issue in Markdown generation:
  - Analyzed cause of image URL element loss, found layout model might delete image URL elements
  - Modified layout prompts to add requirement for "preserving image elements", explicitly requiring layout model not to delete or modify any image URL elements
  - Added detailed logging in `generate_markdown` method to track image URL status before and after layout model processing
  - Ensured image URL elements are correctly preserved during Markdown generation
- Updated project documentation:
  - Created `image_url_issue_plan.md` analysis plan file documenting problem analysis and solution
  - Updated AI development progress record with 2026-02-27 development record
  - Ensured image URL elements are correctly preserved during Markdown generation

## 2026-02-26

- Separated semantic analysis functionality:
  - Separated semantic analysis from Translator class, created independent SemanticAnalyzer base class and AipingSemanticAnalyzer derived class
  - Implemented SemanticAnalyzerFactory to create different types of semantic analyzer instances
  - Modified `translation_service.py` to add `get_semantic_analyzer` method for creating semantic analyzer instances
  - Updated `merge_semantic_blocks_with_llm` function to use `semantic_analyzer` parameter instead of `translator` parameter
  - Ensured translation service directly calls semantic analyzer for semantic analysis instead of indirectly through translator
- Optimized Markdown generator instantiation:
  - Modified Markdown generator creation code in `translation_service.py` to use `create_markdown_generator` function instead of direct instantiation
  - Added import statement for `create_markdown_generator` function
  - Ensured corresponding Markdown generator is automatically used based on selected translation API type
  - Supported aiping and silicon_flow API types for Markdown generation
- Verified changes:
  - Ran all test cases to ensure code changes don't break existing functionality
  - Verified different translation API type Markdown generators can be correctly created and used
  - Ensured all test cases pass for better code quality

## 2026-02-19

- Added multi-threaded parallel translation:
  - Added thread pool in `translation_service.py` for parallel translation of text blocks and table cells
  - Implemented thread-safe result collection and processing
  - Maintained original order of translation results
  - Supported parallel translation of table cells
- Added configuration parameters:
  - Added `MAX_WORKERS` parameter in `config.py` to control maximum thread count
  - Added `TRANSLATION_BATCH_SIZE` parameter in `config.py` to control translation batch size
  - Supported overriding default values with environment variables
- Optimized batch size:
  - Increased batch_size from 5 to 10 in `text_processing.py` for better batch processing efficiency
- Added test cases:
  - Created `test_thread_safety.py` to test thread safety
  - Created `test_performance_multithread.py` to test multi-threading performance
  - Added multi-threading functionality test in `test_translation_service.py`
- Regression testing:
  - Executed all test cases to ensure code changes don't break existing functionality
  - Verified multi-threading functionality works correctly
  - Ensured all test cases pass for better code quality

## 2026-02-19

- Added batch semantic analysis:
  - Added `batch_analyze_semantic_relationship` method and `_generate_batch_semantic_analysis_prompt` method in `translator.py`
  - Implemented batch semantic analysis in `aiping_translator.py` with streaming response and error handling
  - Implemented batch semantic analysis in `silicon_flow_translator.py` with non-streaming response and error handling
  - Optimized batch semantic analysis prompts with detailed analysis criteria and output requirements
- Added batch semantic analysis test cases:
  - Created `test_batch_semantic_analysis.py` with complete batch semantic analysis test cases
  - Tested basic functionality, error handling, retry mechanism, and edge cases
  - Ensured tests cover various batch semantic analysis scenarios
- Added list item continuation test:
  - Created `test_list_item_continuation.py` to test semantic analysis of list item continuation
- Added performance test:
  - Created `test_performance_batch_analysis.py` to test batch semantic analysis performance
- Regression testing:
  - Executed all test cases to ensure code changes don't break existing functionality
  - Verified batch semantic analysis functionality works correctly
  - Ensured all test cases pass for better code quality

## 2026-02-09

- Optimized Word and Markdown generator chart insertion:
  - Removed self.bbox property from MergedBlock class to simplify code structure
  - Implemented chart insertion based on original block position for better chart positioning accuracy
  - Unified chart insertion logic between Word and Markdown generators for consistency
  - Removed unnecessary border calculation and sorting code to simplify code structure
- Fixed table insertion position issue:
  - Modified `translate_tables` method in `translation_service.py` to return PdfTable objects instead of dictionaries
  - Updated `_add_table` method in `docx_generator.py` to use PdfTable object properties
  - Updated `_convert_table_to_markdown` method in `markdown_generator.py` to use PdfTable object properties
  - Updated table handling code in `pdf_generator.py` to use PdfTable object properties
  - Ensured table bbox information is correctly preserved throughout processing
- Updated test cases:
  - Modified `test_markdown_table.py` to use PdfTable and PdfCell objects
  - Modified `test_generate_pdf_with_tables` method in `test_pdf_generator.py` to use PdfTable and PdfCell objects
  - Ensured test cases are consistent with code changes to verify table handling functionality
- Regression testing:
  - Executed all test cases to ensure code changes don't break existing functionality
  - Verified table and chart insertion functionality works correctly
  - Ensured all test cases pass for better code quality

## 2026-02-07

- Optimized text continuity judgment prompts:
  - Modified semantic analysis prompts in `translator.py` to add explicit title recognition rules
  - Detailed title semantic features like conciseness, generality, and guidance
  - Explicitly instructed LLM not to merge titles with other text blocks
  - Provided specific title and non-title examples
- Added title recognition test cases:
  - Added TestTitleRecognition class in `test_semantic_merge_extended.py`
  - Included three test cases testing title not merging with body, body not merging with title, title not merging with title
  - Ensured tests cover various title and body combinations
- Optimized Markdown generator prompts:
  - Modified prompts in `markdown_generator.py` to add requirement for not returning code block markers
  - Explicitly instructed LLM not to add `markdown ` or any other code block markers at the beginning or end of output
  - Ensured generated Markdown text format is correct for subsequent processing
- Optimized test case update prompts:
  - Restructured `update_test_case.md` with detailed test case design principles and best practices
  - Provided test case examples and failed case handling processes
  - Enhanced test case maintenance and management guide
- Optimized documentation update prompts:
  - Restructured `update_doc.md` with detailed code change analysis steps
  - Provided documentation update guide and best practices
  - enhanced verification checklist and documentation update process
- Optimized regression testing prompts:
  - Restructured `regression_testing.md` with detailed regression testing guide
  - Provided test environment preparation, execution flow, and result analysis steps
  - Enhanced failed case handling and regression testing best practices
- Optimized code submission prompts:
  - Restructured `submit.md` with detailed code submission process and guide
  - Provided commit message specification and branch management suggestions
  - Enhanced common problem handling and submission best practices
- Other optimizations:
  - Improved frontend UI by adding vertical spacing to download buttons
  - Optimized error handling by removing fallback, directly returning error messages
  - Ensured all test cases pass for better code quality

## 2026-02-06

- Implemented Markdown output format:
  - Created `markdown_generator.py` module supporting Markdown document generation based on layout model
  - Implemented table-to-Markdown conversion supporting correct table format
  - Implemented chart position sorting and insertion ensuring charts appear in correct positions
  - Supported element insertion within text blocks to handle complex layouts
- Optimized Markdown download:
  - Implemented zip package download for Markdown files and images
  - Updated frontend display logic to ensure download button displays correct text
  - Ensured "all" translation option includes Markdown download
- Optimized test configuration:
  - Created pytest.ini configuration file supporting test type separation
  - Implemented automatic test service management including start and stop
  - Added Markdown-related test files covering download, chart position, and table generation functionality
- Updated configuration and environment variables:
  - Added layout model configuration variables
  - Updated environment variable names for clarity
  - Ensured configuration system consistency

## 2026-02-05

- Fixed Word generation chart position issue:
  - Optimized DocxGenerator class to sort page elements by vertical position
  - Added table processing logic to organize tables by page number
  - Implemented element insertion within text blocks
  - Improved page element processing order to ensure charts and tables appear in correct positions
- Cleaned up test code:
  - Changed return statements to assert statements in `test_style_extraction.py`
  - Changed return statements to assert statements in `test_same_language_optimization.py`
  - Ensured all test functions use assert statements for assertions to avoid return value warnings
- Updated project documentation:
  - Updated project rules documentation with modular development, priority for building data models, and reducing dictionary object usage
  - Updated project rules documentation with detailed code structure related rules
  - Updated development progress documentation with object property access syntax usage
- Updated tech stack specification:
  - Removed pdfplumber and Baidu Translation API
  - Added camelot-py[cv], opencv-python, python-docx, and other dependencies
- Updated directory structure:
  - Added new directories and files, removed non-existent directories and files
  - Reflected current file organization of the project

## 2026-02-04

- Optimized system prompts:
  - Added rule 10: Do not translate URLs, keep them as is
  - Added rule 11: Do not translate code blocks, keep them as is
- Improved header/footer identification logic:
  - Increased frequency threshold from 50% to 70%
  - Added position filtering logic to only consider text in top and bottom regions
  - Improved header/footer identification accuracy
- Added semantic merge toggle:
  - Added "Enable Semantic Block Merge" checkbox in web interface
  - Added `semantic_merge` parameter in translation service
  - Implemented semantic merge and non-merge translation modes
- Optimized semantic merge related code:
  - Improved `merge_semantic_blocks` function to calculate and record max width and height of merged blocks
  - Optimized `process_merged_blocks` and `process_original_blocks` methods
  - Added comprehensive test coverage for semantic merging
  - Improved translation coherence and quality

## 2026-02-02

- Replaced pdfplumber with camelot-py for improved table extraction
- Implemented coordinate system conversion logic to solve coordinate differences between camelot-py and PyMuPDF
- Updated dependencies to add camelot-py[cv], ghostscript, and opencv-python
- Fixed related errors and test cases to ensure table extraction works correctly
- Updated project documentation to reflect tech stack changes
- Optimized PDF extractor:
  - Modified `__init__` method to accept `pdf_path` parameter and extract metadata during initialization
  - Added `get_metadata` method to extract PDF metadata
  - Updated extraction methods to use instance attributes
  - Removed `extract_page_text` method
  - Added `total_pages` attribute for quick access to page count
- Fixed API timeout error:
  - Added 30-second timeout setting for OpenAI client
  - Implemented 3 retry mechanism with 2-second intervals
- Fixed XML compatibility error:
  - Added `_clean_xml_compatible_text` method to remove non-XML compatible characters
  - Updated text adding methods to use cleaning function
- Other fixes:
  - Added os module import in `table_processor.py`
  - Fixed exception handling to correctly raise FileNotFoundError
  - Updated `translation_service.py` to use `total_pages` attribute
  - Added new test cases to verify `total_pages` attribute and other new functionality

## 2026-01-28

- Added translation model configuration support:
  - Added AIPING_MODEL and SILICON_FLOW_MODEL configuration in .env file
  - Added corresponding configuration items in config.py
  - Updated translation_service.py to use configured model parameters
  - Supported overriding default models via environment variables
- Removed hardcoded default values from translator classes:
  - Removed hardcoded default values in aiping_translator.py
  - Removed hardcoded default values in silicon_flow_translator.py
  - Unified default value management through configuration system
- Removed Baidu Translation related code and options:
  - Removed Baidu Translation configuration from config.py
  - Removed Baidu Translation configuration from .env file
  - Removed Baidu Translation option from templates/index.html
  - Removed Baidu Translation handling logic from services/translation_service.py
  - Deleted modules/baidu_translator.py file
  - Removed Baidu Translation references from test files
  - Deleted tests/test_baidu_translator.py file
  - Updated README.md to remove Baidu Translation related content
- Optimized system prompts and user prompts:
  - Added `_generate_system_prompt` and `_generate_user_prompt` methods in translator.py base class
  - Unified prompt format to eliminate code duplication
  - Updated aiping_translator.py to use base class prompt generation methods
  - Updated silicon_flow_translator.py to use base class prompt generation methods
- Updated project documentation:
  - Updated README.md with feature list and tech stack
  - Updated requirement.md with translation API support information
  - Updated AI development progress record

## 2026-01-27

- Implemented Word document generation:
  - Created docx_generator.py module to generate Word documents based on merged translation results
  - Added python-docx dependency to requirements.txt
  - Supported preserving original fonts, sizes, colors, and styles
  - Supported image extraction and insertion into Word documents
  - Supported page section breaks and page breaks
  - Fixed blank page issue in Word document generation
- Optimized document style handling:
  - Fixed font size issue to ensure correct font sizes are used
  - Fixed color issue to ensure only correct text parts display in green
  - Optimized font style inheritance and application
- Simplified Word generation process:
  - Only use merged translation results to generate Word documents
  - Removed Word generation from split results functionality
  - Improved generation efficiency and document quality
- Added output format selection:
  - Added PDF, Word, and Both options in web interface
  - Updated backend logic to support multi-format output
  - Ensured consistent download button styles
- Fixed related issues:
  - Fixed Task object missing add_attachment method issue
  - Optimized image extraction and processing logic
  - Improved overall system stability

## 2026-01-26

- Fixed text block loss issue:
  - Fixed parenthesis position error in merge condition in merge_semantic_blocks function
  - Original condition logic error caused body blocks to be incorrectly processed and lost
  - After fixing parenthesis position, all body blocks can be correctly merged and translated
- Simplified PDF translation tool workflow:
  - Filter all non-body blocks immediately after text extraction
  - Simplified merge_semantic_blocks function to remove all non-body block processing logic
  - Subsequent merge, split, and translation processes only need to process body blocks without considering non-body blocks
  - Improved code readability and maintainability
- Added 13 new semantic merge extended test cases:
  - test_merge_consecutive_body_blocks - Test consecutive body block merging
  - test_merge_blocks_with_sentence_continuation_lowercase - Test sentence continuation starting with lowercase
  - test_merge_blocks_with_sentence_continuation_punctuation - Test sentence continuation starting with punctuation
  - test_no_merge_when_sentence_ends - Test no merging when sentence ends
  - test_no_merge_when_vertical_distance_large - Test no merging when vertical distance is large
  - test_merge_multiple_sequential_blocks - Test multiple sequential block merging
  - test_empty_blocks_list - Test empty list input
  - test_single_block - Test single block
  - test_is_sentence_continuation - Test sentence continuation detection function
  - test_split_with_english_words - Test English word integrity protection
  - test_split_with_punctuation_adjustment - Test punctuation position adjustment
  - test_split_empty_translation - Test empty translation result handling
  - test_filter_non_body_blocks - Test non-body block filtering
- Fixed 4 failing test cases:
  - test_progress.py - Fixed import error
  - test_font_rendering - Fixed PDF generator format error
  - test_process_translation_with_page_range - Fixed temporary file issue
  - test_translate_api - Fixed test data file path and patch path error
- Achieved 100% test pass rate:
  - Total tests: 98
  - Passed: 98
  - Failed: 0

## 2026-01-24

- Optimized text splitting logic to ensure left quotes, brackets, book title marks and other paired characters don't appear at sentence ends
- Improved adjust_split_position function to add checking for left paired characters
- Enhanced split_translated_result function to ensure no left paired characters appear at block ends in final split results
- Added auxiliary function is_left_pair_character to identify left paired characters that shouldn't appear at sentence ends
- Updated test scripts to verify optimization effectiveness

## 2026-01-18

- Initial version released
- Implemented PDF text extraction
- Supported aiping, Silicon Flow translation APIs
- Implemented PDF generation
- Provided Web interface
