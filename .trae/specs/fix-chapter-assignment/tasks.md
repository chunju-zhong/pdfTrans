# PDF翻译工具 - 跨页面文本块章节分配错误修复 - 实现计划

## [x] Task 1: 移除MergedBlock中的章节信息提取
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 修改 `models/merged_block.py` 文件
  - 移除MergedBlock类中从第一个原始块提取章节信息的代码
  - 保持其他属性的提取逻辑不变
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证MergedBlock不再提取章节信息
  - `programmatic` TR-1.2: 验证原始块的章节信息保持不变
- **Notes**: 确保移除章节信息提取后，其他功能不受影响

## [x] Task 2: 确保拆分合并块时使用原始块的章节信息
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改 `services/translation_service.py` 文件
  - 确保在 `process_merged_blocks` 方法中，拆分后的块正确继承原始块的章节信息
  - 验证拆分后的块的章节属性与原始块一致
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证拆分后的块继承了原始块的章节信息
  - `programmatic` TR-2.2: 验证跨页面的块被分配到正确的章节
- **Notes**: 重点检查 `process_merged_blocks` 方法中的章节信息复制逻辑

## [x] Task 3: 修改Markdown生成逻辑使用文本块的章节信息
- **Priority**: P0
- **Depends On**: Task 1, Task 2
- **Description**: 
  - 修改 `modules/markdown_generator.py` 文件
  - 确保在生成Markdown时，使用每个文本块的实际章节信息
  - 验证跨页面的文本块被添加到正确的章节中
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证Markdown生成时使用文本块的章节信息
  - `human-judgment` TR-3.2: 验证生成的Markdown文件中跨页面文本块的章节归属正确
- **Notes**: 重点检查 `_generate_chapter_markdowns` 方法中的章节分配逻辑

## [x] Task 4: 测试修复效果
- **Priority**: P1
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 运行系统处理包含跨页面文本块的PDF文档
  - 验证生成的Markdown文件中章节分配是否正确
  - 检查系统其他功能是否正常运行
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证跨页面文本块的章节分配正确
  - `human-judgment` TR-4.2: 验证生成的Markdown文件结构正确
- **Notes**: 使用包含跨页面文本块的测试文档进行验证