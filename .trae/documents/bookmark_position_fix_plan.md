# 书签位置信息提取修复计划

## [ ] 任务1: 分析书签目标格式
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 分析PyMuPDF返回的不同类型的书签目标格式
  - 确定如何从不同类型的目标中提取位置信息
  - 识别当前提取逻辑的问题所在
- **Success Criteria**:
  - 理解不同类型的书签目标格式
  - 确定从每种格式中提取位置信息的方法
- **Test Requirements**:
  - `programmatic` TR-1.1: 测试不同类型的书签目标格式
  - `human-judgement` TR-1.2: 确认提取逻辑的正确性
- **Notes**: 参考PyMuPDF文档，了解不同类型的目标格式

## [ ] 任务2: 修复位置信息提取逻辑
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 修改_extract_position方法，处理不同类型的书签目标
  - 为/Fit类型的目标提供默认位置信息
  - 确保位置信息被正确提取和存储
- **Success Criteria**:
  - 能够从不同类型的书签目标中提取位置信息
  - 为没有直接位置信息的目标提供合理的默认值
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证不同类型目标的位置信息提取
  - `programmatic` TR-2.2: 验证章节对象的position属性
- **Notes**: 考虑不同类型的目标格式，如/Fit、/FitH、/FitV等

## [ ] 任务3: 验证修复效果
- **Priority**: P1
- **Depends On**: 任务2
- **Description**:
  - 运行测试用例验证位置信息提取逻辑
  - 检查实际PDF文档的书签位置信息提取
  - 验证章节归属逻辑是否正确使用位置信息
- **Success Criteria**:
  - 所有测试用例通过
  - 实际PDF文档的书签位置信息被正确提取
  - 章节归属逻辑正确使用位置信息
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证测试用例通过
  - `human-judgement` TR-3.2: 验证实际PDF文档的位置信息提取
- **Notes**: 使用包含不同类型书签目标的PDF文档进行测试

## [ ] 任务4: 优化日志记录
- **Priority**: P2
- **Depends On**: 任务3
- **Description**:
  - 优化位置信息提取的日志记录
  - 确保日志能够清晰反映位置信息的提取过程
- **Success Criteria**:
  - 日志包含详细的位置信息提取过程
  - 日志能够帮助调试和验证位置信息提取
- **Test Requirements**:
  - `human-judgement` TR-4.1: 验证日志的清晰度和有用性
- **Notes**: 在调试模式下输出详细日志