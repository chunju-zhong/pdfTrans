# PDF翻译工具 - 章节Markdown生成优化实现计划

## [x] Task 1: 修改语义合并逻辑，确保不同章节的块不被合并
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 修改`utils/text_processing.py`中的`merge_semantic_blocks`和`merge_semantic_blocks_with_llm`函数
  - 在合并逻辑中添加章节检查，确保只有相同章节的文本块才会被合并
  - 当遇到不同章节的文本块时，结束当前合并块并开始新的合并块
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证不同章节的文本块不会被合并到同一个语义块中
  - `programmatic` TR-1.2: 验证相同章节的文本块仍然会根据语义关系被正确合并
- **Notes**: 需要确保章节信息在合并过程中被正确传递和检查

## [x] Task 2: 修改Markdown生成器，使用合并块数据生成章节Markdown
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改`modules/markdown_generator.py`中的`_generate_chapter_markdowns`方法
  - 按章节组织合并块数据，而不是原始文本块
  - 修改`_process_chapter_pages`方法，使用合并块数据处理章节内容
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证章节Markdown生成使用合并块数据
  - `programmatic` TR-2.2: 验证生成的Markdown文档内容与合并块内容一致
- **Notes**: 需要确保合并块的章节信息被正确识别和使用

## [x] Task 3: 确保合并块保留原始块的章节信息
- **Priority**: P1
- **Depends On**: Task 1
- **Description**: 
  - 确保`MergedBlock`对象保留原始块的章节信息
  - 当创建新的合并块时，继承第一个原始块的章节信息
  - 确保合并块的章节信息与原始块一致
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证合并块的章节信息与原始块一致
  - `programmatic` TR-3.2: 验证不同章节的合并块具有不同的章节信息
- **Notes**: 章节信息包括chapter_id、chapter_title、chapter_level和chapter_number

## [x] Task 4: 测试和验证
- **Priority**: P1
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 编写测试用例验证优化后的功能
  - 测试包含多个章节的PDF文档
  - 验证章节边界清晰，不同章节的内容不被合并
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-4.1: 运行测试用例验证语义合并逻辑
  - `programmatic` TR-4.2: 运行测试用例验证章节Markdown生成
  - `human-judgment` TR-4.3: 人工检查生成的Markdown文档，确保章节边界清晰
- **Notes**: 测试应覆盖不同章节结构的PDF文档

## 测试结果
所有测试都通过了，包括：
- `test_markdown_generator.py`: 9个测试用例全部通过
- `test_semantic_merge.py`: 3个测试用例全部通过

这表明优化后的功能正常工作，语义合并逻辑能够正确处理章节边界，Markdown生成器能够使用合并块数据生成章节Markdown文件。