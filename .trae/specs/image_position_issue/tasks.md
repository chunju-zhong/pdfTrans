# 图片插入位置错误问题分析 - 实施计划

## [ ] 任务1: 分析图片位置计算逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 分析MarkdownGenerator和DocxGenerator中的图片位置计算逻辑
  - 重点关注_find_chart_position和_find_merged_block方法
  - 理解当前的位置计算算法
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证_find_chart_position方法是否正确计算图片前后的文本块
  - `programmatic` TR-1.2: 验证_find_merged_block方法是否正确找到包含原始块的合并块
- **Notes**: 关注坐标计算和合并块查找的逻辑

## [ ] 任务2: 分析合并块的合并逻辑
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 
  - 分析文本块合并的逻辑，了解哪些文本块会被合并
  - 检查合并块的original_blocks属性是否包含正确的原始块信息
  - 确认合并块的位置信息是否准确
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证合并块是否正确包含原始块
  - `programmatic` TR-2.2: 验证合并块的位置信息是否反映原始块的位置
- **Notes**: 关注合并块的创建和属性设置逻辑

## [ ] 任务3: 分析12页图片的具体位置问题
- **Priority**: P0
- **Depends On**: 任务1, 任务2
- **Description**: 
  - 分析12页图片的位置信息和周围文本块
  - 检查"initial Mission is achieved"和"Figure 1: Agentic AI problem-solving process"对应的文本块
  - 分析图片位置计算的具体过程
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `human-judgment` TR-3.1: 确认12页图片的实际位置和期望位置
  - `programmatic` TR-3.2: 验证图片位置计算的具体步骤和结果
- **Notes**: 重点关注这两个文本之间的图片插入逻辑

## [ ] 任务4: 识别根本原因
- **Priority**: P0
- **Depends On**: 任务1, 任务2, 任务3
- **Description**: 
  - 综合分析所有信息，识别导致图片位置错误的根本原因
  - 确定是位置计算逻辑问题还是合并块处理问题
  - 提供详细的根因分析报告
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `human-judgment` TR-4.1: 确认根因分析的合理性
  - `programmatic` TR-4.2: 验证根因分析的逻辑正确性
- **Notes**: 考虑多种可能的原因，进行全面分析

## [ ] 任务5: 提供修复建议
- **Priority**: P1
- **Depends On**: 任务4
- **Description**: 
  - 基于根因分析，提供具体的修复建议
  - 包括代码修改的具体位置和方法
  - 提供验证修复效果的测试方案
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `human-judgment` TR-5.1: 评估修复建议的可行性
  - `programmatic` TR-5.2: 验证修复方案的逻辑正确性
- **Notes**: 确保修复方案对现有代码的影响最小