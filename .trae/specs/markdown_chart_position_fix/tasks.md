# Markdown生成器图表位置修复 - 实现计划

## [ ] 任务1: 分析章节内容组织逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 分析当前按章节组织内容的逻辑
  - 理解如何将文本块、图像和表格按章节分组
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `human-judgment` TR-1.1: 理解当前章节内容组织逻辑
  - `human-judgment` TR-1.2: 识别图表位置处理的缺失点
- **Notes**: 需要深入理解`_generate_chapter_markdowns`方法的实现

## [ ] 任务2: 重构章节内容组织逻辑，支持图表位置处理
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 修改`_generate_chapter_markdowns`方法，按页码组织章节内容
  - 为每个章节创建页面元素列表，包含文本块、图像和表格
  - 按页码和位置排序元素
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-2.1: 章节内容按页码正确组织
  - `programmatic` TR-2.2: 元素按位置正确排序
- **Notes**: 需要确保元素的位置信息正确保留

## [ ] 任务3: 重用_process_page_elements方法处理图表位置
- **Priority**: P0
- **Depends On**: 任务2
- **Description**:
  - 修改`_generate_chapter_markdowns`方法，为每个章节调用`_process_page_elements`
  - 确保传递正确的参数给`_process_page_elements`
  - 处理章节内的所有页面元素
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-3.1: `_process_page_elements`方法被正确调用
  - `human-judgment` TR-3.2: 图表位置正确插入
- **Notes**: 需要确保传递正确的原始文本块和页面元素

## [ ] 任务4: 测试和验证
- **Priority**: P1
- **Depends On**: 任务3
- **Description**:
  - 运行所有测试用例，确保修改后的代码正常工作
  - 测试包含图表的PDF文档，验证图表位置是否正确
  - 验证按章节生成的Markdown文档质量
- **Acceptance Criteria Addressed**: AC-1, AC-3
- **Test Requirements**:
  - `programmatic` TR-4.1: 所有测试用例通过
  - `human-judgment` TR-4.2: 图表在章节Markdown中位置正确
- **Notes**: 需要测试有图表和无图表的情况