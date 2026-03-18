# TODO List

## High Priority
- [x] Optimize glossary extraction prompts, add NO_GLOSSARY identifier handling
- [x] Implement glossary file operations (load and save)
- [x] Optimize button style, reduce button height
- [x] Fix button click not responding issue
- [x] Set "Use LLM for semantic judgment" to checked by default
- [x] Optimize chapter Markdown generation, fix chapter mapping logic and content organization
- [x] Fix parameter name errors in test cases
- [x] Implement PyMuPDF table extraction
- [x] Implement title and body separation
- [x] Optimize UI text, change "按章节拆分Markdown" to "按章节翻译Markdown"
- [x] Enhance logging system, add detailed logs for table translation and drawing process
- [x] Implement translation progress system refactoring
- [x] Implement two-phase semantic block merging
- [x] Optimize text block merging algorithm
- [ ] Further optimize glossary extraction accuracy and efficiency

## Medium Priority
- [x] Fix test_pdf_page_translation.py::TestPdfPageTranslationIntegration::test_process_translation_with_no_matching_pages
  - Reason: Mock verification failed, update_progress call count incorrect
  - Solution: Update mock verification logic in tests
- [x] Fix test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_single_title
  - Reason: Block count changed after code changes, test assertions don't match actual results
  - Solution: Update test assertions or analyze code changes to confirm expected behavior changes
- [x] Fix test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_multi_block_title
  - Reason: Block count changed after code changes
  - Solution: Update test assertions or analyze code changes to confirm expected behavior changes
- [x] Fix test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_llm
  - Reason: Block count changed after code changes
  - Solution: Update test assertions or analyze code changes to confirm expected behavior changes
- [x] Fix test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_llm_multi_block_title
  - Reason: Block count changed after code changes
  - Solution: Update test assertions or analyze code changes to confirm expected behavior changes
- [x] Fix test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_multiple_chapters
  - Reason: Block count changed after code changes
  - Solution: Update test assertions or analyze code changes to confirm expected behavior changes
- [x] Fix test_semantic_analyzer.py merged block count assertions
- [x] Create test_two_phase_merge.py to test two-phase merging
- [x] Create test_split_sentence.py to test sentence splitting
- [x] Create test_list_detection.py to test list detection
- [ ] Expand glossary file operations, support more file formats
- [ ] Improve test coverage
- [ ] Optimize user interface for better user experience
- [ ] Improve system performance and stability
- [ ] Further optimize chapter Markdown generation, improve generation quality
- [ ] Expand table extraction, support more complex tables and table styles

## Low Priority
- [ ] Expand glossary extraction support for more translation platforms
- [ ] Optimize API call strategy, improve translation efficiency
- [ ] Improve documentation, add user guides
- [ ] Code refactoring, improve maintainability
- [ ] Explore more PDF processing technologies, further improve extraction quality
