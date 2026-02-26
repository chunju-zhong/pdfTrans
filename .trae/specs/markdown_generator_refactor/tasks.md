# PDF翻译工具 - Markdown生成器重构实现计划

## [ ] Task 1: 重构MarkdownGenerator类为基类
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 重构现有的MarkdownGenerator类，保留核心功能
  - 确保向后兼容性
  - 优化代码结构，为派生类做好准备
  - 确保支持硅基流动等使用标准方法调用的平台
- **Acceptance Criteria Addressed**: AC-1, AC-4
- **Test Requirements**:
  - `programmatic` TR-1.1: 重构后的MarkdownGenerator类应能正常工作，功能与重构前一致
  - `human-judgement` TR-1.2: 代码应符合项目的代码风格和结构规范
- **Notes**: 保持核心方法不变，只进行必要的重构以支持派生类

## [ ] Task 2: 创建AipingMarkdownGenerator派生类
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 创建AipingMarkdownGenerator类，继承自MarkdownGenerator
  - 实现aiping特定的参数设置，特别是在extra_body中定义费用优先策略
  - 重写必要的方法以支持aiping特定参数
- **Acceptance Criteria Addressed**: AC-2, AC-4
- **Test Requirements**:
  - `programmatic` TR-2.1: AipingMarkdownGenerator应能正确设置费用优先策略
  - `programmatic` TR-2.2: AipingMarkdownGenerator应能正常生成Markdown文档
  - `human-judgement` TR-2.3: 代码应符合项目的代码风格和结构规范
- **Notes**: 确保费用优先策略正确设置在extra_body中

## [ ] Task 3: 实现工厂方法或创建函数
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 实现一个工厂方法或创建函数，根据用户选择的翻译API返回相应的生成器实例
  - 提供简单的接口供其他模块调用
  - 确保工厂方法能正确处理不同的API类型
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-3.1: 工厂方法应能根据API类型返回正确的生成器实例
  - `programmatic` TR-3.2: 工厂方法应能处理无效的API类型并给出适当的错误提示
  - `human-judgement` TR-3.3: 代码应符合项目的代码风格和结构规范
- **Notes**: 考虑添加适当的错误处理和参数验证

## [ ] Task 4: 测试和验证
- **Priority**: P1
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 测试重构后的代码，确保所有功能正常工作
  - 验证AipingMarkdownGenerator的费用优先策略设置
  - 验证工厂方法的正确性
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 所有生成器类应能正常生成Markdown文档
  - `programmatic` TR-4.2: AipingMarkdownGenerator应正确设置费用优先策略
  - `programmatic` TR-4.3: 工厂方法应返回正确的生成器实例
- **Notes**: 测试时使用实际的API调用或模拟API响应

## [ ] Task 5: 文档更新
- **Priority**: P2
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 更新相关文档，说明如何使用新的生成器类和工厂方法
  - 添加代码注释，提高代码的可读性
  - 确保文档与实现保持一致
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `human-judgement` TR-5.1: 文档应清晰说明如何使用新的生成器类和工厂方法
  - `human-judgement` TR-5.2: 代码应包含适当的注释和文档字符串
- **Notes**: 保持文档简洁明了，重点说明使用方法和参数设置