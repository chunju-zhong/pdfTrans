# Checklist

- [x] test_llm_extractor_multi_bbox.py 6 个用例全部通过
- [x] test_llm_extractor_parse_response.py 11 个用例全部通过
- [x] test_llm_ocr.py::TestMixedFormulaTextRendering 10 个用例全部通过
- [x] test_ocr_extractor.py::TestTableHtmlParser::test_parse_simple_table 通过
- [x] test_output_filename.py::test_process_translation_sync_passes_output_filename 通过
- [x] test_python_review_fixes.py 中 TestParseHtmlTableReturnCheck 和 TestComputeTableLayoutSideEffects 3 个用例通过
- [x] _generate_outputs 方法签名包含 layout_model 参数
- [x] 所有修复不影响其他现有测试（运行完整测试套件无回归，819 passed）
