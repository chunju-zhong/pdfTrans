# Tasks

- [x] Task 1: 分析现有代码结构
  - [x] 1.1 详细阅读 merge_semantic_blocks_with_llm 方法的实现
  - [x] 1.2 了解 batch_analyze_semantic_relationship 接口
  - [x] 1.3 确定需要修改的代码位置

- [x] Task 2: 实现并行批量分析方法 parallel_batch_analyze
  - [x] 2.1 在 text_processing.py 中添加 parallel_batch_analyze 方法
  - [x] 2.2 实现 ThreadPoolExecutor 并行调用逻辑
  - [x] 2.3 实现批次结果按顺序收集逻辑
  - [x] 2.4 添加重试机制和错误处理

- [x] Task 3: 实现两阶段合并方法
  - [x] 3.1 创建 merge_semantic_blocks_with_llm_two_phase 方法
  - [x] 3.2 实现阶段1：并行获取所有判断结果
  - [x] 3.3 实现阶段2：根据预存结果顺序合并
  - [x] 3.4 保持与原逻辑一致的合并规则

- [x] Task 4: 配置开关和集成
  - [x] 4.1 在 phase_config 或 config.py 中添加配置项
  - [x] 4.2 修改 translation_service.py 支持配置切换

- [x] Task 5: 单元测试
  - [x] 5.1 编写 parallel_batch_analyze 方法的单元测试
  - [x] 5.2 编写两阶段合并方法的单元测试
  - [x] 5.3 验证合并结果与原逻辑一致

- [x] Task 6: 性能测试
  - [x] 6.1 对比串行和并行的执行时间
  - [x] 6.2 验证性能提升目标（3-5倍）

# Task Dependencies

- [Task 2] 依赖 [Task 1]
- [Task 3] 依赖 [Task 1, Task 2]
- [Task 4] 依赖 [Task 3]
- [Task 5] 依赖 [Task 3]
- [Task 6] 依赖 [Task 4, Task 5]
