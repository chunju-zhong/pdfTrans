# 修复测试套件回归失败 Spec

## Why
代码重构后（OcrBlock 提取到 llm_response_parser.py、_TableHtmlParser 行格式变更、PdfGenerator 方法委派到 text_renderer、_generate_outputs 新增参数），6 组共 17 个测试用例因返回值/签名/属性访问方式变更而失败，需同步更新测试以匹配当前代码结构。

## What Changes
- 修复 `test_llm_extractor_multi_bbox.py`（6 个用例）：`_parse_ref_tags_to_blocks` 现在返回 `list[OcrBlock]`（2 元组），而非 `(text_blocks, tables, images)` 三元组
- 修复 `test_llm_extractor_parse_response.py`（2 个用例）：`_parse_response` 内部逻辑已重构，mock 路径需适配当前委派调用链
- 修复 `test_llm_ocr.py::TestMixedFormulaTextRendering`（5 个用例）：`PdfGenerator` 的静态方法改为实例方法，通过 `self.text_renderer` 委派，直接类调用报 `AttributeError`
- 修复 `test_ocr_extractor.py::TestTableHtmlParser::test_parse_simple_table`（1 个用例）：`_TableHtmlParser.rows` 中每个单元格从 `str` 变为 `(text, rowspan, colspan)` 三元组
- 修复 `test_output_filename.py::test_process_translation_sync_passes_output_filename`（1 个用例）：`_generate_outputs` 不接受 `layout_model` 参数，导致 `process_translation_sync` 调用失败
- 修复 `test_python_review_fixes.py`（3 个用例）：`inspect.getsource` 检查的目标方法已变为薄委派层，实际逻辑在 `llm_response_parser.py` 和 `llm_table_parser.py` 中

## Impact
- Affected code: 6 个测试文件
- Affected source files: `llm_extractor.py`（需给 `_generate_outputs` 加 `layout_model` 参数）、`llm_response_parser.py`、`llm_table_parser.py`、`paddle_extractor.py`、`pdf_generator.py`、`translation_service.py`
- 不影响生产代码行为，仅修复测试/补充缺失参数

## ADDED Requirements

### Requirement: _generate_outputs 接受 layout_model 参数
`TranslationService._generate_outputs` 方法 SHALL 接受 `layout_model` 可选参数并传递给下游调用，以匹配 `process_translation_sync` 的调用签名。

#### Scenario: process_translation_sync 传递 layout_model
- **WHEN** `process_translation_sync` 使用 `layout_model=layout_model` 调用 `_generate_outputs`
- **THEN** `_generate_outputs` 不抛出 `TypeError`，正确传递参数

## MODIFIED Requirements

### Requirement: _parse_ref_tags_to_blocks 返回值解包
测试 SHALL 使用 `_parse_ref_tags_to_blocks` 的实际返回值格式（`list[OcrBlock]`），而非三元组 `(text_blocks, tables, images)`。映射为模型对象需通过 `_map_ocr_blocks_to_models` 完成。

### Requirement: _parse_response mock 链路
测试 SHALL 适配 `_parse_response` 内部的实际调用链路：当 JSON 解析返回空列表后，`_parse_markdown_to_blocks` 需被正确 mock，且回退逻辑需匹配当前实现。

### Requirement: PdfGenerator 静态方法测试
测试 SHALL 通过实例调用 `PdfGenerator` 的方法（如 `_contains_latex_formula`），而非类级别调用，因为方法已委派到 `self.text_renderer`。

### Requirement: _TableHtmlParser.rows 格式
测试 SHALL 匹配 `_TableHtmlParser.rows` 中每个单元格的 `(text, rowspan, colspan)` 三元组格式。

### Requirement: 代码结构检查目标模块
测试 SHALL 检查实际实现所在的模块（`llm_response_parser.py`、`llm_table_parser.py`），而非薄委派层（`llm_extractor.py`）。
