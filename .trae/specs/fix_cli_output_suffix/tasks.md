# PDF翻译工具 - 修复CLI输出文件后缀处理问题 - 实现计划

## [x] Task 1: 分析当前输出路径处理逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 分析`cli/translate_command.py`中的输出路径处理逻辑
  - 理解当前如何处理用户指定的输出路径
  - 确定需要修改的位置
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证当前输出路径处理逻辑
  - `programmatic` TR-1.2: 确认需要修改的代码位置

## [x] Task 2: 实现智能后缀处理函数
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 实现`get_output_path_with_correct_suffix`函数
  - 函数应根据输出格式自动添加正确的文件后缀
  - 支持PDF、Word、Markdown三种格式
  - 对于已指定正确后缀的情况保持不变
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-2.1: 测试Markdown格式自动添加.zip后缀
  - `programmatic` TR-2.2: 测试PDF格式自动添加.pdf后缀
  - `programmatic` TR-2.3: 测试Word格式自动添加.docx后缀
  - `programmatic` TR-2.4: 测试已指定正确后缀时保持不变

## [x] Task 3: 集成智能后缀处理
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 在`translate_handler`函数中集成智能后缀处理
  - 在用户指定输出路径时调用智能后缀处理函数
  - 确保文件复制逻辑使用处理后的输出路径
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证完整的翻译流程
  - `programmatic` TR-3.2: 确认输出文件正确生成

## [x] Task 4: 测试修复效果
- **Priority**: P1
- **Depends On**: Task 3
- **Description**: 
  - 测试不同输出格式的智能后缀处理
  - 验证已指定正确后缀的情况
  - 确保翻译结果正确生成
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 测试Markdown格式智能后缀处理
  - `programmatic` TR-4.2: 测试PDF格式智能后缀处理
  - `programmatic` TR-4.3: 测试Word格式智能后缀处理
  - `programmatic` TR-4.4: 测试已指定正确后缀的情况
  - `programmatic` TR-4.5: 测试翻译结果的正确性