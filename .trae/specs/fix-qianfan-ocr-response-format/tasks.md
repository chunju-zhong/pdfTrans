# Tasks

- [ ] Task 1: 添加调试日志，记录 qianfan-ocr 完整原始响应到文件
  - [ ] 在 `_extract_page` 中（响应接收后、`_parse_response` 调用前）将 `result_text` 完整写入调试文件
  - [ ] 文件命名如 `debug_qianfan_ocr_page_{page_num}_response.txt`

- [ ] Task 2: 运行一次 qianfan-ocr OCR 提取，收集完整响应
  - [ ] 使用用户报告的 PDF 运行一次提取
  - [ ] 收集调试文件

- [ ] Task 3: 分析完整响应，定位根因
  - [ ] 检查响应是否以 `{` 开头，或前面有 ` thinking` 等前缀
  - [ ] 手动验证 JSON 解析是否成功（`json.loads`/`_extract_json`）
  - [ ] 验证 JSON schema 字段名是否与 `_parse_json_to_blocks` 期望一致
  - [ ] 确认根因并记录到 spec 的 Findings 章节

- [ ] Task 4: 清理调试代码
  - [ ] 移除调试文件写入逻辑