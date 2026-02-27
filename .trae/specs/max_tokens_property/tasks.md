# Max Tokens Property Enhancement - Implementation Plan

## [x] Task 1: 修改 AipingSemanticAnalyzer 类，添加 max_tokens 属性
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 AipingSemanticAnalyzer 类中添加 max_tokens 类属性，默认值为1024（用于单个语义分析）
  - 在 AipingSemanticAnalyzer 类中添加 batch_max_tokens 类属性，默认值为2048（用于批量语义分析，需要处理更多文本）
  - 修改 API 调用中的 max_tokens 参数，使用类属性值
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证默认情况下使用1024和2048作为max_tokens值
  - `programmatic` TR-1.2: 验证外部设置max_tokens后，API调用使用设置的值
- **Notes**: 保持与现有API调用结构的兼容性

## [x] Task 2: 修改 AipingTranslator 类，添加 max_tokens 属性
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 AipingTranslator 类中添加 max_tokens 类属性，默认值为8192
  - 修改 API 调用中的 max_tokens 参数，使用类属性值
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证默认情况下使用8192作为max_tokens值
  - `programmatic` TR-2.2: 验证外部设置max_tokens后，API调用使用设置的值
- **Notes**: 保持与现有API调用结构的兼容性

## [x] Task 3: 修改 MarkdownGenerator 类，添加 max_tokens 属性
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 MarkdownGenerator 类中添加 max_tokens 类属性，默认值为8192
  - 修改 API 调用中的 max_tokens 参数，使用类属性值
- **Acceptance Criteria Addressed**: AC-5, AC-6
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证默认情况下使用8192作为max_tokens值
  - `programmatic` TR-3.2: 验证外部设置max_tokens后，API调用使用设置的值
- **Notes**: 保持与现有API调用结构的兼容性

## [x] Task 4: 修改 SemanticAnalyzer 类，添加 max_tokens 属性
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 SemanticAnalyzer 类中添加 max_tokens 类属性，默认值为1024（用于单个语义分析）
  - 在 SemanticAnalyzer 类中添加 batch_max_tokens 类属性，默认值为2048（用于批量语义分析，需要处理更多文本）
  - 修改 API 调用中的 max_tokens 参数，使用类属性值
- **Acceptance Criteria Addressed**: AC-7, AC-8
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证默认情况下使用1024和2048作为max_tokens值
  - `programmatic` TR-4.2: 验证外部设置max_tokens后，API调用使用设置的值
- **Notes**: 保持与现有API调用结构的兼容性

## [x] Task 5: 修改 SiliconFlowTranslator 类，添加 max_tokens 属性
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 SiliconFlowTranslator 类中添加 max_tokens 类属性，默认值为8192
  - 修改 API 调用中的 max_tokens 参数，使用类属性值
- **Acceptance Criteria Addressed**: AC-9, AC-10
- **Test Requirements**:
  - `programmatic` TR-5.1: 验证默认情况下使用8192作为max_tokens值
  - `programmatic` TR-5.2: 验证外部设置max_tokens后，API调用使用设置的值
- **Notes**: 保持与现有API调用结构的兼容性

## [x] Task 6: 编写测试脚本验证修改
- **Priority**: P1
- **Depends On**: Task 1, Task 2, Task 3, Task 4, Task 5
- **Description**: 
  - 创建测试脚本，验证所有修改后的类都能正确使用默认max_tokens值
  - 验证外部设置max_tokens后，API调用使用设置的值
  - 确保修改后的代码与现有功能兼容
- **Acceptance Criteria Addressed**: 所有AC
- **Test Requirements**:
  - `programmatic` TR-6.1: 验证所有类的默认max_tokens值设置正确
  - `programmatic` TR-6.2: 验证所有类都能接受外部设置的max_tokens值
  - `programmatic` TR-6.3: 验证修改后的代码与现有功能兼容
- **Notes**: 测试脚本应覆盖所有修改的类和方法