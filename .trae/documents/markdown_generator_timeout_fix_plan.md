# Markdown Generator 超时问题修复计划

## 问题分析
根据用户提供的日志，调用 Aiping API 生成 Markdown 时出现了无限循环的问题：
- HTTP 请求返回了 200 OK
- 但代码在处理流式响应时卡住了
- 服务器持续返回进度查询的 200 响应，但生成过程一直不结束

## 根因分析
检查 `markdown_generator.py` 中的 `_call_api` 方法，发现以下潜在问题：
1. 流式响应处理循环 `for chunk in stream:` 没有超时机制
2. 没有检测响应是否已经完成的逻辑
3. 可能 Aiping API 的响应格式与预期不同，导致 `finish_reason` 永远不会被设置

## 修复计划

### [x] 任务 1: 添加流式响应超时机制
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 `_call_api` 方法中添加超时机制
  - 使用 `time.time()` 跟踪开始时间
  - 在循环中检查是否超过预设的最大处理时间
  - 如果超时，抛出异常或返回部分结果
- **Success Criteria**: 当处理时间超过设定阈值时，方法能够正常退出并返回结果或抛出异常
- **Test Requirements**:
  - `programmatic` TR-1.1: 当 API 响应超时时，方法能够在设定的时间内退出
  - `programmatic` TR-1.2: 超时后能够返回合理的错误信息

### [x] 任务 2: 改进流式响应处理逻辑
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 改进 `for chunk in stream:` 循环的处理逻辑
  - 添加对响应结束的检测
  - 处理可能的异常情况
  - 确保即使在异常情况下也能正确退出循环
- **Success Criteria**: 流式响应处理能够正确结束，不会无限循环
- **Test Requirements**:
  - `programmatic` TR-2.1: 方法能够正确处理正常的流式响应
  - `programmatic` TR-2.2: 方法能够正确处理异常的流式响应
  - `programmatic` TR-2.3: 方法能够在各种情况下正确退出循环

### [x] 任务 3: 优化 Aiping API 响应处理
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**:
  - 特别针对 Aiping API 的响应格式进行优化
  - 检查 Aiping API 是否有特殊的响应格式或结束标记
  - 确保能够正确解析 Aiping API 返回的 `finish_reason`
- **Success Criteria**: Aiping API 的响应能够被正确处理，不会导致无限循环
- **Test Requirements**:
  - `programmatic` TR-3.1: 方法能够正确处理 Aiping API 的响应
  - `programmatic` TR-3.2: 方法能够正确识别 Aiping API 响应的结束标记

### [x] 任务 4: 添加日志和监控
- **Priority**: P2
- **Depends On**: 任务 3
- **Description**:
  - 在 `_call_api` 方法中添加更详细的日志
  - 记录流式响应的处理状态
  - 记录处理时间和超时情况
- **Success Criteria**: 能够通过日志清楚地了解流式响应的处理过程和可能的问题
- **Test Requirements**:
  - `human-judgment` TR-4.1: 日志能够清晰地反映流式响应的处理过程
  - `human-judgment` TR-4.2: 日志能够帮助诊断可能的问题

### [x] 任务 5: 测试和验证
- **Priority**: P0
- **Depends On**: 任务 4
- **Description**:
  - 运行完整的测试套件，确保修复不会破坏现有功能
  - 特别测试 Aiping API 的调用情况
  - 测试超时情况的处理
- **Success Criteria**: 所有测试通过，Aiping API 调用能够正常完成或在超时时合理退出
- **Test Requirements**:
  - `programmatic` TR-5.1: 所有现有测试通过
  - `programmatic` TR-5.2: Aiping API 调用测试通过
  - `programmatic` TR-5.3: 超时处理测试通过

## 预期结果
- 修复后，Aiping API 调用生成 Markdown 时不会无限循环
- 当 API 响应超时时，方法能够合理退出并返回错误信息
- 保持与现有代码的兼容性，不会破坏其他功能
- 提供清晰的日志，便于诊断可能的问题