# 章节位置信息提取修复计划

## [ ] 任务1: 分析位置信息提取问题
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 分析PyMuPDF中dest对象的结构
  - 确定正确的位置信息提取方法
  - 检查当前代码的提取逻辑
- **Success Criteria**:
  - 理解dest对象的正确结构
  - 识别当前提取逻辑的问题
- **Test Requirements**:
  - `programmatic` TR-1.1: 测试不同类型的dest对象结构
  - `human-judgement` TR-1.2: 确认提取逻辑的正确性
- **Notes**: 参考PyMuPDF文档，了解dest对象的结构

## [ ] 任务2: 修复位置信息提取逻辑
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 修改_build_chapter_tree方法，正确提取位置信息
  - 处理不同类型的dest对象
  - 确保位置信息被正确存储到Chapter对象中
- **Success Criteria**:
  - 位置信息能够正确提取
  - 所有章节都有正确的position属性
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证位置信息提取的正确性
  - `programmatic` TR-2.2: 验证章节对象的position属性
- **Notes**: 考虑dest可能是元组或字典的情况

## [ ] 任务3: 验证章节归属逻辑
- **Priority**: P1
- **Depends On**: 任务2
- **Description**:
  - 运行测试用例验证章节归属逻辑
  - 检查跨章节页的文本块归属
  - 验证位置信息是否被正确使用
- **Success Criteria**:
  - 跨章节页的文本块归属正确
  - 位置信息被正确用于章节归属判断
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证跨章节页的文本块归属
  - `programmatic` TR-3.2: 验证位置信息的使用
- **Notes**: 使用包含跨章节页的PDF文档进行测试

## [ ] 任务4: 优化日志记录
- **Priority**: P2
- **Depends On**: 任务3
- **Description**:
  - 添加详细的位置信息日志
  - 确保日志能够清晰反映章节归属的判断过程
- **Success Criteria**:
  - 日志包含位置信息
  - 日志能够清晰反映章节归属的判断过程
- **Test Requirements**:
  - `human-judgement` TR-4.1: 验证日志的清晰度和有用性
- **Notes**: 在调试模式下输出详细日志