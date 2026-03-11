# Markdown生成器重构 - 实现计划

## [ ] 任务1: 分析现有代码结构
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 分析`generate_markdown`方法中按页组织翻译结果的代码
  - 识别可重用的逻辑部分
- **Success Criteria**:
  - 理解现有代码的逻辑流程
  - 识别可以抽取为独立函数的代码块
- **Test Requirements**:
  - `human-judgment` TR-1.1: 理解现有代码逻辑
  - `human-judgment` TR-1.2: 识别可重用的代码块
- **Notes**: 需要确保抽取的函数能够在不同上下文中使用

## [ ] 任务2: 创建`_process_pages`方法
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 创建新的`_process_pages`方法，封装按页组织和处理内容的逻辑
  - 该方法应接受翻译内容、图像、输出文本列表等参数
  - 实现页码组织、元素处理和文本构建的逻辑
- **Success Criteria**:
  - `_process_pages`方法能够正确处理页面元素
  - 方法参数设计合理，能够在不同上下文中使用
- **Test Requirements**:
  - `programmatic` TR-2.1: 方法能够正确处理页面元素
  - `human-judgment` TR-2.2: 代码结构清晰，易于理解
- **Notes**: 需要确保方法能够处理空数据的情况

## [ ] 任务3: 修改`generate_markdown`方法，使用新的`_process_pages`方法
- **Priority**: P0
- **Depends On**: 任务2
- **Description**:
  - 修改`generate_markdown`方法，替换原有的按页处理逻辑
  - 调用新的`_process_pages`方法处理页面内容
  - 保持原有功能不变
- **Success Criteria**:
  - `generate_markdown`方法功能正常
  - 代码更加简洁，减少重复
- **Test Requirements**:
  - `programmatic` TR-3.1: 所有测试用例通过
  - `human-judgment` TR-3.2: 代码结构更加清晰
- **Notes**: 需要确保向后兼容性

## [ ] 任务4: 修改`_generate_chapter_markdowns`方法，使用新的`_process_pages`方法
- **Priority**: P0
- **Depends On**: 任务3
- **Description**:
  - 修改`_generate_chapter_markdowns`方法，使用新的`_process_pages`方法
  - 确保章节内的页面处理逻辑与原逻辑一致
- **Success Criteria**:
  - `_generate_chapter_markdowns`方法功能正常
  - 代码更加简洁，减少重复
- **Test Requirements**:
  - `programmatic` TR-4.1: 所有测试用例通过
  - `human-judgment` TR-4.2: 代码结构更加清晰
- **Notes**: 需要确保章节处理逻辑的正确性

## [ ] 任务5: 测试和验证
- **Priority**: P1
- **Depends On**: 任务4
- **Description**:
  - 运行所有测试用例，确保修改后的代码正常工作
  - 验证按章节生成Markdown的功能
  - 验证图表位置处理的正确性
- **Success Criteria**:
  - 所有测试用例通过
  - 按章节生成的Markdown文档质量良好
- **Test Requirements**:
  - `programmatic` TR-5.1: 所有测试用例通过
  - `human-judgment` TR-5.2: 生成的Markdown文档符合预期
- **Notes**: 需要测试有图表和无图表的情况