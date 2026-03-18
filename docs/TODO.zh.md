# TODO列表

## 高优先级
- [x] 优化术语提取提示词，添加NO_GLOSSARY标识处理
- [x] 实现术语表文件操作功能（加载和保存）
- [x] 优化按钮样式，减小按钮高度
- [x] 修复按钮点击无响应问题
- [x] 将"使用大语言模型进行语义判断"设置为默认勾选
- [x] 优化章节Markdown生成功能，修复章节映射逻辑和内容组织
- [x] 修复测试用例中的参数名错误
- [x] 实现PyMuPDF表格提取功能
- [x] 实现标题与正文区分功能
- [x] 优化UI文本，将"按章节拆分Markdown"修改为"按章节翻译Markdown"
- [x] 增强日志系统，添加表格翻译和绘制流程的详细日志
- [x] 实现翻译进度系统重构
- [x] 实现语义块两阶段合并功能
- [x] 优化文本块合并算法
- [ ] 进一步优化术语提取的准确性和效率

## 中优先级
- [x] 修复 test_pdf_page_translation.py::TestPdfPageTranslationIntegration::test_process_translation_with_no_matching_pages
  - 原因：mock验证失败，update_progress调用次数不正确
  - 方案：更新测试中的mock验证逻辑
- [x] 修复 test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_single_title
  - 原因：代码变更后合并块数量变化，测试断言与实际结果不符
  - 方案：更新测试断言或分析代码变更确认预期行为变化
- [x] 修复 test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_multi_block_title
  - 原因：代码变更后合并块数量变化
  - 方案：更新测试断言或分析代码变更确认预期行为变化
- [x] 修复 test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_llm
  - 原因：代码变更后合并块数量变化
  - 方案：更新测试断言或分析代码变更确认预期行为变化
- [x] 修复 test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_llm_multi_block_title
  - 原因：代码变更后合并块数量变化
  - 方案：更新测试断言或分析代码变更确认预期行为变化
- [x] 修复 test_title_body_separation.py::TestTitleBodySeparation::test_merge_semantic_blocks_with_multiple_chapters
  - 原因：代码变更后合并块数量变化
  - 方案：更新测试断言或分析代码变更确认预期行为变化
- [x] 修复 test_semantic_analyzer.py 合并块数量断言
- [x] 创建 test_two_phase_merge.py 测试两阶段合并功能
- [x] 创建 test_split_sentence.py 测试句子拆分功能
- [x] 创建 test_list_detection.py 测试列表检测功能
- [ ] 扩展术语表文件操作功能，支持更多文件格式
- [ ] 完善测试用例，提高测试覆盖率
- [ ] 优化用户界面，提供更好的用户体验
- [ ] 改进系统性能和稳定性
- [ ] 进一步优化章节Markdown生成功能，提高生成质量
- [ ] 扩展表格提取功能，支持更多复杂表格和表格样式

## 低优先级
- [ ] 扩展支持更多翻译平台的术语提取
- [ ] 优化API调用策略，提高翻译效率
- [ ] 完善文档，添加使用指南
- [ ] 代码重构，提高代码可维护性
- [ ] 探索更多PDF处理技术，进一步提高提取质量
