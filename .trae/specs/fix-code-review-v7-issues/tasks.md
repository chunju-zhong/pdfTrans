# Tasks
- [x] Task 1: 修复 sentinel 数据损坏 bug（Issue 1, HIGH）
  - [x] SubTask 1.1: `modules/translator.py` `_parse_format_result` 失败分支返回 `[]` 而非 `["fallback_invalid_format"]`
  - [x] SubTask 1.2: 更新注释说明返回 `[]` 触发整页回退（日志消息保持准确）
  - [x] SubTask 1.3: 更新 `tests/test_translator.py` `test_parse_format_result_without_markers_insufficient_lines` 断言为 `assert parsed == []`
  - [x] SubTask 1.4: 新增测试 `test_format_blocks_single_block_empty_llm_response` 验证单块+空响应时回退到原文

- [x] Task 2: 删除 _build_short_english_hint 死代码（Issue 2, MEDIUM）
  - [x] SubTask 2.1: 删除 `modules/ocr/llm_extractor.py` 中 `_SOURCE_LANG_ENGLISH_NAMES` 字典
  - [x] SubTask 2.2: 删除 `_build_short_english_hint` 方法
  - [x] SubTask 2.3: 简化 `_extract_page` DeepSeek-OCR 分支，直接 `user_text = DEEPSEEK_OCR_PROMPT`

- [x] Task 3: format_blocks 异常上报 + target_lang 提示 + classify_llm_error（Issues 3+5+6, MEDIUM/LOW）
  - [x] SubTask 3.1: `modules/translator.py` `format_blocks` 移除内部 try/except，让异常向上抛出
  - [x] SubTask 3.2: `modules/translator.py` `format_blocks` 在 user_prompt 中注入目标语言名称（使用 `self.supported_languages` 映射）
  - [x] SubTask 3.3: `services/translation_content.py` 调用方使用 `classify_llm_error` 生成友好消息并 `task.add_warning`
  - [x] SubTask 3.4: 更新 `tests/test_translator.py` `test_formatting_api_error_fallback` 改为 `pytest.raises` 验证异常向上抛出
  - [x] SubTask 3.5: 移除 `modules/translator.py` 中未使用的 `classify_llm_error` 导入

- [x] Task 4: 删除 llm_response_parser.py 未使用导入（Issue 4, LOW）
  - [x] SubTask 4.1: 删除 `modules/ocr/llm_response_parser.py` 的 `import numpy as np` 和 `from PIL import Image`

# Task Dependencies
- Task 1 与 Task 2 无依赖，可并行
- Task 3 依赖 Task 1 完成（format_blocks 行为变更需协调）
- Task 4 独立，可并行

# Validation
- [x] `python3 -m py_compile modules/translator.py modules/ocr/llm_extractor.py modules/ocr/llm_response_parser.py services/translation_content.py` 通过
- [x] `pytest tests/test_translator.py` 24/25 通过（test_silicon_flow_translate 失败为先前 streaming 切换遗留，与本轮修改无关）
- [x] `pytest tests/test_semantic_analyzer_json_extraction.py` 15/15 通过
