# Markdown Generator 截断警告修复计划

## 问题分析
根据用户提供的日志，Aiping API 调用生成 Markdown 时出现了以下问题：
- Aiping API 调用成功完成，收到了结束标记 `finish_reason: stop`
- 生成的 Markdown 不完整
- 但没有在前台显示截断警告

## 根因分析
检查 `markdown_generator.py` 中的代码，发现以下问题：
1. `_call_api` 方法中，`truncated` 标志的设置逻辑为 `truncated = finish_reason == "length"`
2. 但 Aiping API 返回的 `finish_reason` 是 "stop"，即使响应可能被截断
3. 因此 `truncated` 标志被设置为 `False`，导致没有显示截断警告

## 修复计划

### [x] 任务 1: 改进截断检测逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 修改 `_call_api` 方法中的截断检测逻辑
  - 考虑 Aiping API 的特殊情况
  - 添加额外的截断检测机制，如检查生成的文本长度与预期的差异
- **Success Criteria**: 当 Aiping API 响应被截断时，`truncated` 标志能够正确设置为 `True`
- **Test Requirements**:
  - `programmatic` TR-1.1: 当 `finish_reason` 为 "stop" 但文本不完整时，`truncated` 标志为 `True`
  - `programmatic` TR-1.2: 当 `finish_reason` 为 "length" 时，`truncated` 标志为 `True`
  - `programmatic` TR-1.3: 当响应正常完成时，`truncated` 标志为 `False`

### [x] 任务 2: 增强截断警告显示
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 确保截断警告能够在前台显示
  - 检查 `TranslationService` 中是否正确处理截断信息并生成警告
  - 确保警告信息能够传递到前端
- **Success Criteria**: 当 Markdown 生成被截断时，前台能够显示相应的警告信息
- **Test Requirements**:
  - `programmatic` TR-2.1: 当 `truncated` 为 `True` 时，系统能够生成截断警告
  - `human-judgment` TR-2.2: 警告信息清晰明了，能够在前台显示

### [x] 任务 3: 优化 Aiping API 响应处理
- **Priority**: P1
- **Depends On**: 任务 1
- **Description**:
  - 进一步优化 Aiping API 的响应处理
  - 检查 Aiping API 的 `finish_reason` 可能的取值
  - 确保能够正确识别各种情况下的截断
- **Success Criteria**: 能够正确处理 Aiping API 的各种响应情况，包括截断
- **Test Requirements**:
  - `programmatic` TR-3.1: 能够正确处理 Aiping API 的各种 `finish_reason` 值
  - `programmatic` TR-3.2: 能够正确识别 Aiping API 的截断情况

### [x] 任务 4: 测试和验证
- **Priority**: P0
- **Depends On**: 任务 2, 任务 3
- **Description**:
  - 运行完整的测试套件，确保修复不会破坏现有功能
  - 特别测试 Aiping API 的截断检测和警告显示
  - 测试各种情况下的截断检测
- **Success Criteria**: 所有测试通过，截断检测和警告显示功能正常工作
- **Test Requirements**:
  - `programmatic` TR-4.1: 所有现有测试通过
  - `programmatic` TR-4.2: 截断检测测试通过
  - `programmatic` TR-4.3: 警告显示测试通过

## 预期结果
- 修复后，当 Aiping API 响应被截断时，能够正确检测并显示截断警告
- 生成的 Markdown 不完整时，用户能够得到明确的警告信息
- 保持与现有代码的兼容性，不会破坏其他功能
- 提供清晰的日志，便于诊断可能的问题