# 修复CLI模式下源文件被删除的问题 - 实现计划

## [ ] Task 1: 分析文件清理逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 分析 `_complete_task` 方法中的文件清理逻辑
  - 分析异常处理中的文件清理逻辑
  - 确定如何区分CLI模式和Web模式
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-1.1: 确认 `_complete_task` 方法当前的文件删除逻辑
  - `programmatic` TR-1.2: 确认异常处理中的文件删除逻辑
- **Notes**: 重点关注 `remove_file(input_filepath)` 调用

## [ ] Task 2: 修改 process_translation_sync 方法
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改 `process_translation_sync` 方法，添加参数标识是否为CLI模式
  - 传递此参数到 `_complete_task` 方法
- **Acceptance Criteria Addressed**: AC-1, AC-3
- **Test Requirements**:
  - `programmatic` TR-2.1: 确保 `process_translation_sync` 方法接受新参数
  - `programmatic` TR-2.2: 确保参数正确传递给 `_complete_task`
- **Notes**: 保持向后兼容性

## [ ] Task 3: 修改 _complete_task 方法
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 修改 `_complete_task` 方法，添加参数标识是否为CLI模式
  - 只有非CLI模式时才删除文件
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: CLI模式下不删除源文件
  - `programmatic` TR-3.2: Web模式下删除临时文件
- **Notes**: 确保Web模式的文件清理逻辑不变

## [ ] Task 4: 修改异常处理逻辑
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 修改异常处理中的文件清理逻辑
  - 只有非CLI模式时才删除文件
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-4.1: 异常情况下CLI模式不删除源文件
  - `programmatic` TR-4.2: 异常情况下Web模式删除临时文件
- **Notes**: 确保异常处理的文件清理逻辑与正常流程一致

## [ ] Task 5: 修改CLI调用
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 修改 `cli/translate_command.py` 中的调用，传递CLI模式标识
- **Acceptance Criteria Addressed**: AC-1, AC-3
- **Test Requirements**:
  - `programmatic` TR-5.1: CLI调用传递正确的模式标识
- **Notes**: 确保所有CLI调用都传递正确的参数

## [ ] Task 6: 测试修复效果
- **Priority**: P1
- **Depends On**: Task 3, Task 4, Task 5
- **Description**: 
  - 测试CLI模式下源文件不被删除
  - 测试Web模式下临时文件被清理
  - 测试翻译失败时源文件不被删除
  - 测试翻译成功时生成输出文件
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-6.1: CLI模式翻译成功后源文件存在
  - `programmatic` TR-6.2: CLI模式翻译失败后源文件存在
  - `programmatic` TR-6.3: Web模式翻译后临时文件被删除
  - `programmatic` TR-6.4: 翻译成功后生成正确的输出文件
- **Notes**: 确保所有测试场景都覆盖
