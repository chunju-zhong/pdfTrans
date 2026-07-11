# Tasks

- [x] Task 1: 修复 test_llm_extractor_multi_bbox.py（6个用例）
  - [x] 1.1: 将 `text_blocks, _, _ = extractor._parse_ref_tags_to_blocks(...)` 改为先获取 `ocr_blocks = extractor._parse_ref_tags_to_blocks(...)`，再调用 `text_blocks, _, _ = extractor._map_ocr_blocks_to_models(ocr_blocks, page_num=1, page_info=MOCK_PAGE_INFO)`
  - [x] 1.2: 更新所有断言：`text_blocks[i].block_text` → 通过 _map_ocr_blocks_to_models 映射后检查 TextBlock
  - [x] 1.3: 验证 6 个用例全部通过

- [x] Task 2: 修复 test_llm_extractor_parse_response.py（2个用例）
  - [x] 2.1: 修复 `TestParseResponseJsonFallback.test_empty_json_result_falls_back_to_markdown`：JSON解析成功但内容为空时返回None，不触发Markdown回退
  - [x] 2.2: 修复 `TestExtractJsonBraceFinding`：文本中间的合法JSON片段会被成功提取
  - [x] 2.3: 验证 11 个用例全部通过

- [x] Task 3: 修复 test_llm_ocr.py::TestMixedFormulaTextRendering（5个用例）
  - [x] 3.1: 将 `PdfGenerator._contains_latex_formula(...)` 类调用改为 `PdfGenerator()._contains_latex_formula(...)` 实例调用
  - [x] 3.2: `_preprocess_latex_for_mathtext` 仍为 @staticmethod，无需修改
  - [x] 3.3: 验证 TestMixedFormulaTextRendering 全部 10 个用例通过

- [x] Task 4: 修复 test_ocr_extractor.py::TestTableHtmlParser::test_parse_simple_table
  - [x] 4.1: 更新断言：`parser.rows[0] == [('A', 1, 1), ('B', 1, 1)]`
  - [x] 4.2: 更新断言：`parser.rows[1] == [('1', 1, 1), ('2', 1, 1)]`
  - [x] 4.3: 验证通过

- [x] Task 5: 修复 test_output_filename.py + 源码 _generate_outputs 签名（1个用例）
  - [x] 5.1: 在 `translation_service.py` 的 `_generate_outputs` 方法签名中添加 `layout_model=None` 参数
  - [x] 5.2: 将 `layout_model` 传递给 `generate_output_files` 调用链
  - [x] 5.3: `generate_output_files` 已有 `layout_model` 参数，无需修改
  - [x] 5.4: 验证测试通过

- [x] Task 6: 修复 test_python_review_fixes.py（3个用例）
  - [x] 6.1: `TestParseHtmlTableReturnCheck`：改为 `inspect.getsource(LlmOcrResponseParser._map_ocr_blocks_to_models)`
  - [x] 6.2: `TestComputeTableLayoutSideEffects.test_docstring_mentions_side_effects`：改为 `LlmTableParser._compute_table_layout.__doc__`
  - [x] 6.3: `TestComputeTableLayoutSideEffects.test_docstring_mentions_estimated_lines`：同上
  - [x] 6.4: 验证 3 个用例通过

# Task Dependencies

- Task 1-4, 6 互相独立，可并行
- Task 5 涉及源码修改，与其他任务独立
