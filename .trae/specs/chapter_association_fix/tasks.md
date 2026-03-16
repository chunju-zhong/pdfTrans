# 文本块章节归属准确性修复 - 实现计划

## [x] 任务1: 分析当前章节归属逻辑的问题
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 深入分析ChapterIdentifier类中的章节归属逻辑
  - 识别跨章节页处理的具体问题
  - 确定需要修改的代码位置
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证当前逻辑对跨章节页的处理结果
  - `programmatic` TR-1.2: 验证当前逻辑对错误页码归属的处理结果
- **Notes**: 需要重点关注_build_chapter_mapping和associate_text_blocks方法

## [x] 任务2: 实现基于PDF书签页码和位置数据的章节归属逻辑
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 修改ChapterIdentifier类，只使用PDF书签页码信息和页面位置数据（如x, y坐标）精确定位章节归属
  - 实现基于文本块垂直位置与书签位置数据对比的章节归属逻辑
  - 实现跨章节页的准确处理
  - 保持与现有代码的兼容性
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-4
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证跨章节页文本块的正确归属
  - `programmatic` TR-2.2: 验证错误页码归属的修复
  - `programmatic` TR-2.3: 验证向后兼容性
- **Notes**: 使用PyMuPDF的get_toc(simple=False)方法获取包含位置数据的详细书签信息

## [x] 任务3: 优化性能和日志记录
- **Priority**: P1
- **Depends On**: 任务2
- **Description**: 
  - 优化章节归属逻辑的性能
  - 添加详细的日志记录，便于调试和验证
  - 确保性能影响在可接受范围内
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证性能影响不超过10%
  - `human-judgement` TR-3.2: 验证日志记录的清晰度和有用性
- **Notes**: 可以考虑缓存章节信息，减少重复计算

## [x] 任务4: 编写测试用例
- **Priority**: P1
- **Depends On**: 任务2
- **Description**: 
  - 编写针对跨章节页的测试用例
  - 编写针对错误页码归属的测试用例
  - 编写性能测试用例
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证测试用例覆盖所有场景
  - `programmatic` TR-4.2: 验证测试用例的准确性
- **Notes**: 测试用例应包含各种跨章节页的场景

## [x] 任务5: 验证修复效果
- **Priority**: P1
- **Depends On**: 任务3, 任务4
- **Description**:
  - 运行测试用例验证修复效果
  - 手动验证实际PDF文档的章节归属
  - 性能测试和兼容性测试
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-5.1: 验证所有测试用例通过
  - `human-judgement` TR-5.2: 验证实际PDF文档的章节归属准确性
- **Notes**: 应使用包含跨章节页的实际PDF文档进行测试
- **Status**: 已完成
  - 所有测试用例通过，验证了跨章节页的文本块归属准确性
  - 验证了错误页码归属的修复
  - 验证了向后兼容性
  - 性能测试通过，性能影响在可接受范围内