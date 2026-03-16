# PDF翻译工具 - 多线程并发术语提取功能 - 实现计划

## [x] Task 1: 修改GlossaryService类，实现按页提取文本
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 修改`_extract_text_from_pdf`方法，返回按页组织的文本数据
  - 确保能够获取每个页面的文本内容
- **Acceptance Criteria Addressed**: [AC-1, AC-3]
- **Test Requirements**:
  - `programmatic` TR-1.1: 方法应返回一个字典，键为页码，值为该页面的文本
  - `programmatic` TR-1.2: 确保所有页面的文本都被正确提取
- **Notes**: 保持与现有代码结构的兼容性

## [x] Task 2: 实现多线程并发术语提取
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 使用concurrent.futures模块创建线程池
  - 为每个页面提交术语提取任务
  - 等待所有任务完成并收集结果
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-4]
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证多线程并发处理是否正常工作
  - `programmatic` TR-2.2: 比较多线程和单线程版本的执行时间
  - `human-judgment` TR-2.3: 检查线程安全，确保无冲突
- **Notes**: 线程池大小应根据系统CPU核心数动态调整

## [x] Task 3: 实现术语结果合并、去重和排序
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 合并来自所有页面的术语提取结果
  - 去除重复的术语
  - 对术语进行排序
  - 保持术语表的格式一致性
- **Acceptance Criteria Addressed**: [AC-3, AC-4]
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证合并后的术语表格式正确
  - `programmatic` TR-3.2: 确保重复术语被正确去除
  - `programmatic` TR-3.3: 验证术语已正确排序
- **Notes**: 注意术语的大小写和格式一致性

## [x] Task 4: 实现按页处理时的进度条更新
- **Priority**: P1
- **Depends On**: Task 2
- **Description**: 
  - 在处理每个页面时更新进度信息
  - 确保进度条能够反映当前处理的页面和总页面数
  - 保持与现有进度条系统的兼容性
- **Acceptance Criteria Addressed**: [AC-5]
- **Test Requirements**:
  - `human-judgment` TR-4.1: 验证进度条是否显示按页处理的进度信息
  - `programmatic` TR-4.2: 确保进度更新的准确性
- **Notes**: 注意线程安全，避免并发更新进度信息导致的问题

## [x] Task 5: 测试和优化
- **Priority**: P1
- **Depends On**: Task 3, Task 4
- **Description**: 
  - 测试不同大小PDF文件的术语提取性能
  - 优化线程池大小和任务分配策略
  - 确保在各种情况下的稳定性
- **Acceptance Criteria Addressed**: [AC-2, AC-4]
- **Test Requirements**:
  - `programmatic` TR-5.1: 测试大PDF文件的提取性能
  - `programmatic` TR-5.2: 测试并发处理多个任务的稳定性
- **Notes**: 考虑边缘情况，如空PDF文件或只有一页的PDF文件