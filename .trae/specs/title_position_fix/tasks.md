# PDF章节标题位置识别修复 - The Implementation Plan (Decomposed and Prioritized Task List)

## [ ] Task 1: 研究并实现改进的匹配算法
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 改进`_find_title_position`方法，实现更精确的文本匹配算法
  - 优先寻找与标题完全匹配的单个文本块（考虑空白字符的差异）
  - 然后尝试将多个连续文本块拼接起来匹配标题
  - 避免简单的子字符串匹配导致的误识别
  - 使用Python标准库中的`difflib.SequenceMatcher`来计算文本相似度
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-1.1: 当页面中存在完全匹配的单个文本块时，应该返回该文本块的位置
  - `programmatic` TR-1.2: 当标题跨多个连续文本块时，应该能够识别并返回第一个文本块的位置
  - `programmatic` TR-1.3: 当只有包含子字符串的文本块时，不应该误匹配
  - `human-judgement` TR-1.4: 代码实现应该清晰易读，符合项目规范
- **Notes**: 匹配策略：1) 精确匹配单个文本块；2) 跨多个连续文本块匹配；3) 高相似度匹配（相似度>0.9）；4) 子字符串匹配（仅作为最后的备选）；跨文本块匹配最多尝试拼接3个连续文本块

## [ ] Task 2: 实现候选文本块评分系统
- **Priority**: P1
- **Depends On**: Task 1
- **Description**: 
  - 为每个候选匹配计算综合评分
  - 评分因素包括：文本相似度、匹配类型（精确匹配 vs 部分匹配 vs 跨块匹配）、位置合理性（标题通常在页面上方）
  - 选择评分最高的匹配作为最终结果
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-2.1: 评分系统应该能够正确区分标题和普通文本
  - `programmatic` TR-2.2: 精确匹配的应该获得最高评分
  - `human-judgement` TR-2.3: 评分因子的权重分配应该合理
- **Notes**: 可以设计可配置的权重参数，但初期使用硬编码的合理值

## [ ] Task 3: 编写单元测试
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 为改进后的`_find_title_position`方法编写全面的单元测试
  - 测试精确匹配单个文本块的场景
  - 测试跨多个连续文本块匹配的场景
  - 测试子字符串误匹配的场景（如"Agents and Agent" vs "Introduction to Agents and Agent architectures"）
  - 测试相似度匹配的场景
  - 确保所有测试通过
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-3.1: 单元测试覆盖率应达到80%以上
  - `programmatic` TR-3.2: 所有测试用例都应该通过
  - `human-judgement` TR-3.3: 测试用例应该覆盖各种边界情况
- **Notes**: 可以使用模拟的PDF数据进行测试，避免依赖真实PDF文件

## [ ] Task 4: 集成测试和验证
- **Priority**: P1
- **Depends On**: Task 3
- **Description**: 
  - 使用真实的PDF文件进行集成测试
  - 特别测试包含类似"Agents and Agent"和"Introduction to Agents and Agent architectures"的场景
  - 测试包含跨多个文本块标题的PDF文件
  - 验证文本块、表格、图像关联到章节的正确性
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 集成测试应该通过
  - `human-judgement` TR-4.2: 人工验证章节关联的正确性
  - `human-judgement` TR-4.3: 性能应该与原算法相当或更好
- **Notes**: 可以使用项目中已有的测试PDF文件

## [ ] Task 5: 代码审查和优化
- **Priority**: P2
- **Depends On**: Task 4
- **Description**: 
  - 进行代码审查，确保符合项目规范
  - 优化代码性能和可读性
  - 添加必要的注释和文档
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `human-judgement` TR-5.1: 代码应该符合项目的代码风格和规范
  - `human-judgement` TR-5.2: 代码应该有必要的注释
  - `programmatic` TR-5.3: 代码检查工具应该通过
- **Notes**: 参考项目的PEP 8规范和代码风格指南
