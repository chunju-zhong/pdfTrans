# PDF翻译工具 - 章节图片和表格位置修复 实现计划

## [x] Task 1: 分析现有代码逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 分析`_process_chapter_pages`方法的现有实现
  - 分析`_process_pages`和`_process_page_elements`方法的实现逻辑
  - 确定需要修改的部分
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `human-judgement` TR-1.1: 确认理解了现有代码的逻辑和差异
  - `human-judgement` TR-1.2: 确认了需要修改的部分
- **Notes**: 重点关注元素排序和插入的逻辑差异

## [x] Task 2: 修改`_process_chapter_pages`方法
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改`_process_chapter_pages`方法，使其能够根据元素在页面中的实际位置来排序和插入文本块、图像和表格
  - 参考`_process_page_elements`方法的逻辑，实现元素的正确排序和插入
  - 确保修改后的方法与完整Markdown输出逻辑一致
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证修改后的代码能够正确编译
  - `human-judgement` TR-2.2: 验证修改后的代码逻辑与`_process_page_elements`方法一致
- **Notes**: 保持代码风格与现有代码一致

## [x] Task 3: 测试修复效果
- **Priority**: P1
- **Depends On**: Task 2
- **Description**: 
  - 运行PDF翻译工具，测试按章节生成Markdown功能
  - 验证图片和表格是否正确分配到所在章节
  - 验证图片和表格在章节Markdown中的位置是否正确
  - 对比完整Markdown输出和按章节生成Markdown的结果，确保两者一致
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证按章节生成Markdown功能能够正常运行
  - `human-judgement` TR-3.2: 验证图片和表格被正确分配到所在章节
  - `human-judgement` TR-3.3: 验证图片和表格在章节Markdown中的位置正确
  - `human-judgement` TR-3.4: 验证与完整Markdown输出逻辑一致
- **Notes**: 使用包含多个章节和图片/表格的PDF文档进行测试

## [x] Task 4: 清理和优化代码
- **Priority**: P2
- **Depends On**: Task 3
- **Description**: 
  - 清理修改过程中产生的临时代码和注释
  - 优化代码结构，提高代码可读性和可维护性
  - 确保代码符合项目的代码风格规范
- **Acceptance Criteria Addressed**: NFR-1, NFR-2
- **Test Requirements**:
  - `human-judgement` TR-4.1: 验证代码结构清晰，易于理解
  - `human-judgement` TR-4.2: 验证代码符合项目的代码风格规范
- **Notes**: 保持代码修改的最小化原则，只修改必要的部分