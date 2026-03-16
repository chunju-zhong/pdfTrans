# 章节Markdown生成问题修复 - 实现计划

## [x] Task 1: 检查章节识别和映射逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查 `modules/chapter_identifier.py` 中的章节识别和映射逻辑
  - 确保所有章节（包括嵌套章节）都能被正确识别
  - 验证章节映射逻辑是否正确处理了所有页码
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-1.1: 章节识别逻辑能够检测到PDF中的所有章节，包括嵌套章节
  - `programmatic` TR-1.2: 章节映射逻辑能够为所有页码正确关联对应的章节
- **Notes**: 重点检查章节树的构建和章节映射的生成逻辑

## [x] Task 2: 检查章节内容组织逻辑
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 检查 `modules/markdown_generator.py` 中的章节内容组织逻辑
  - 分析为什么检测到9个章节但只生成了1个章节文件
  - 检查章节内容过滤逻辑，确保所有章节都能被包含
- **Acceptance Criteria Addressed**: [AC-2, AC-3]
- **Test Requirements**:
  - `programmatic` TR-2.1: 章节内容组织逻辑能够为所有章节创建条目
  - `programmatic` TR-2.2: 章节内容组织逻辑能够正确处理嵌套章节
- **Notes**: 重点检查章节内容过滤和清理逻辑

## [x] Task 3: 修复章节内容处理逻辑
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 修复 `modules/markdown_generator.py` 中的章节内容处理逻辑
  - 确保每个章节都能包含完整的文本、图像和表格内容
  - 优化章节内容处理逻辑，避免内容丢失
- **Acceptance Criteria Addressed**: [AC-3]
- **Test Requirements**:
  - `programmatic` TR-3.1: 章节内容处理逻辑能够正确处理文本块
  - `programmatic` TR-3.2: 章节内容处理逻辑能够正确处理图像
  - `programmatic` TR-3.3: 章节内容处理逻辑能够正确处理表格
- **Notes**: 重点检查 `_process_chapter_pages` 方法的实现

## [/] Task 4: 验证修复效果
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 运行章节Markdown生成功能，验证修复效果
  - 检查生成的章节文件数量是否与章节数量一致
  - 检查每个章节文件是否包含完整的内容
  - 检查嵌套章节是否正确生成
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4]
- **Test Requirements**:
  - `human-judgment` TR-4.1: 生成的章节文件数量与章节数量一致
  - `human-judgment` TR-4.2: 每个章节文件包含完整的内容
  - `human-judgment` TR-4.3: 嵌套章节正确生成，文件名包含正确的层级编号
- **Notes**: 使用包含多个章节和嵌套章节的PDF文件进行测试