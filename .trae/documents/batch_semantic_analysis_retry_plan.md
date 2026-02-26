# 批量语义分析结果数量不一致重试机制 - 实现计划

## \[x] 任务 1: 修改 SemanticAnalyzer.batch\_analyze\_semantic\_relationship 方法，实现结果数量不一致时的重试机制

* **优先级**: P0

* **依赖**: 无

* **描述**:

  * 修改 `batch_analyze_semantic_relationship` 方法，当检测到结果数量与输入文本对数量不一致时，进行重试

  * 最多重试3次，每次重试间隔2秒

  * 3次重试后如果结果数量仍然不一致，则将缺少的项记为false

* **成功标准**:

  * 当大模型返回的结果个数与输入文本对数量不一致时，系统会自动重试

  * 重试3次后仍然个数不对，将缺少的项记为false

  * 重试过程中正确记录日志

* **测试要求**:

  * `programmatic` TR-1.1: 模拟大模型返回结果数量不一致的情况，验证系统是否进行重试

  * `programmatic` TR-1.2: 验证3次重试后仍然数量不一致时，系统是否将缺少的项记为false

  * `human-judgement` TR-1.3: 检查日志是否正确记录重试过程

* **注意事项**:

  * 确保重试逻辑与现有的错误处理逻辑（如JSON解析错误、API请求失败）协调工作

  * 保持与现有代码风格一致

## [x] 任务 2: 修改 AipingSemanticAnalyzer.batch_analyze_semantic_relationship 方法，实现相同的重试机制
- **优先级**: P0
- **依赖**: 任务 1
- **描述**:
  - 修改 `AipingSemanticAnalyzer.batch_analyze_semantic_analysis` 方法，实现与基类相同的结果数量不一致时的重试机制
  - 确保重试逻辑与基类一致
- **成功标准**:
  - AipingSemanticAnalyzer 在结果数量不一致时也会进行重试
  - 重试3次后仍然个数不对，将缺少的项记为false
  - 重试过程中正确记录日志
- **测试要求**:
  - `programmatic` TR-2.1: 模拟 Aiping 大模型返回结果数量不一致的情况，验证系统是否进行重试
  - `programmatic` TR-2.2: 验证3次重试后仍然数量不一致时，系统是否将缺少的项记为false
  - `human-judgement` TR-2.3: 检查日志是否正确记录重试过程
- **注意事项**:
  - 确保与基类的实现保持一致
  - 注意 Aiping API 的特殊处理逻辑

## [x] 任务 3: 运行测试，验证实现是否正确
- **优先级**: P1
- **依赖**: 任务 1, 任务 2
- **描述**:
  - 运行现有的语义分析器测试，确保修改后的代码通过所有测试
  - 验证重试机制是否按预期工作
- **成功标准**:
  - 所有语义分析器相关的测试都通过
  - 重试机制在模拟的场景下正确工作
- **测试要求**:
  - `programmatic` TR-3.1: 运行 `tests/test_semantic_analyzer.py` 确保所有测试通过
  - `human-judgement` TR-3.2: 检查测试日志，确认重试逻辑被正确执行
- **注意事项**:
  - 确保测试覆盖各种边缘情况
  - 验证日志记录的完整性

