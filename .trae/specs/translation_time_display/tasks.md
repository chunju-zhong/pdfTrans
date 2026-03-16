# PDF翻译工具 - 前端UI增加显示翻译总耗时功能 - 实现计划

## [x] 任务1: 修改Task模型，添加时间属性
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在Task类中添加start_time和end_time属性
  - 添加计算总耗时的方法
  - 更新to_dict方法，包含总耗时信息
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: Task对象能够正确记录开始和结束时间
  - `programmatic` TR-1.2: Task对象能够正确计算总耗时
- **Notes**: 使用Python的time模块来获取时间戳

## [x] 任务2: 修改翻译服务，记录任务时间
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 
  - 在translation_service.py中，在任务开始时设置start_time
  - 在任务完成、取消或失败时设置end_time
  - 确保所有状态下都能正确处理时间记录
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 任务开始时正确设置start_time
  - `programmatic` TR-2.2: 任务完成、取消或失败时正确设置end_time
- **Notes**: 考虑异步任务的时间记录逻辑

## [x] 任务3: 修改API响应，返回耗时信息
- **Priority**: P0
- **Depends On**: 任务1, 任务2
- **Description**: 
  - 修改app.py中的get_progress路由
  - 在API响应中添加total_time字段
  - 确保在任务进行中、完成、取消或失败时都能返回耗时信息
  - 实时计算当前耗时，即使任务未完成
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: API响应包含total_time字段
  - `programmatic` TR-3.2: total_time值正确反映翻译耗时
  - `programmatic` TR-3.3: 任务进行中时也能返回实时耗时
- **Notes**: 计算耗时为当前时间 - start_time，单位为秒

## [x] 任务4: 修改前端UI，显示耗时信息
- **Priority**: P0
- **Depends On**: 任务3
- **Description**: 
  - 修改前端index.html，在进度显示区域和结果区域添加耗时显示
  - 修改main.js，处理API返回的total_time字段
  - 实现友好的时间格式显示（分:秒）
  - 在进度更新时实时显示当前耗时
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `human-judgment` TR-4.1: 翻译过程中，前端实时显示耗时信息
  - `human-judgment` TR-4.2: 翻译完成后，前端显示总耗时信息
  - `human-judgment` TR-4.3: 耗时显示格式为"翻译总耗时：X分X秒"
- **Notes**: 前端需要处理秒到分:秒的转换