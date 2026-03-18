# Changelog

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
