# PDF翻译工具 - 自动提取术语表功能实现计划

## [ ] Task 1: 为aiping和硅基流动在.env配置文件中添加术语提示模型参数
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 在.env配置文件中为aiping添加术语提示模型名等参数
  - 在.env配置文件中为硅基流动添加术语提示模型名等参数
  - 更新config.py文件以支持读取这些新参数
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: .env文件中包含aiping和硅基流动的术语提示模型参数
  - `programmatic` TR-1.2: config.py能够正确读取这些新参数
- **Notes**: 确保参数命名规范与现有配置保持一致

## [ ] Task 2: 实现基于大语言模型的术语提取接口和类（多平台支持）
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 创建新的接口及类实现术语提取功能
  - 为术语提取实现独立的大语言模型调用模块，不与翻译等其他类共用
  - 设计多平台支持，基于openai接口，支持aiping和硅基流动等不同的大语言模型服务
  - 实现调用大语言模型的接口，发送适当的提示词以提取术语和翻译
  - 确保aiping像其他实现一样支持config中的额外body参数
  - 处理大语言模型的响应，转换为标准的术语表格式
  - 支持从.env文件中读取模型配置，包括术语提示模型名等参数
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-2.1: 能够从示例PDF中提取至少5个专业术语
  - `programmatic` TR-2.2: 提取的术语表格式符合"术语: 翻译"的要求
  - `programmatic` TR-2.3: 支持aiping、硅基流动等多个大语言模型平台
  - `programmatic` TR-2.4: aiping实现支持config中的额外body参数
  - `programmatic` TR-2.5: 能够从.env文件中读取模型配置，包括术语提示模型名等参数
  - `programmatic` TR-2.6: 大语言模型调用模块独立于翻译等其他类
  - `human-judgement` TR-2.7: 提取的术语应具有一定的专业性和代表性
- **Notes**: 保持统一的接口设计，便于后续扩展

## [ ] Task 3: 实现术语提取服务
- **Priority**: P0
- **Depends On**: Task 2
- **Description**:
  - 创建独立的术语提取服务，与PDF提取流程分离
  - 实现从PDF文件中提取文本并调用大语言模型提取术语的逻辑
  - 处理PDF中无明显术语的情况
- **Acceptance Criteria Addressed**: AC-1, AC-4
- **Test Requirements**:
  - `programmatic` TR-3.1: 术语提取服务能正确从PDF中提取术语
  - `programmatic` TR-3.2: 无术语PDF处理时不出现错误
  - `programmatic` TR-3.3: 术语提取服务不影响现有翻译流程
- **Notes**: 注意处理大语言模型调用的超时和错误情况

## [ ] Task 4: 修改前端UI添加提取术语按钮和进度显示
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - 在前端HTML模板中添加"提取术语"功能按钮
  - 实现提取进度对话框，显示提取进度及成功或失败的提示
  - 确保UI风格与现有界面一致
  - 添加适当的提示文字说明功能
  - 实现按钮点击事件，触发术语提取流程
  - 实现术语提取完成后将结果回填入输入框的功能
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `human-judgement` TR-4.1: 按钮位置合理，易于操作
  - `human-judgement` TR-4.2: 界面风格与现有设计一致
  - `programmatic` TR-4.3: 按钮点击事件能正确触发术语提取
  - `programmatic` TR-4.4: 提取进度对话框能正确显示
  - `programmatic` TR-4.5: 提取完成后结果能正确回填入输入框
- **Notes**: 按钮应位于术语表输入框附近

## [ ] Task 5: 实现后端API处理术语提取请求
- **Priority**: P1
- **Depends On**: Task 3, Task 4
- **Description**:
  - 添加新的Flask路由，处理术语提取请求
  - 实现进度更新机制，返回提取进度信息
  - 接收PDF文件信息，调用术语提取工具
  - 返回提取的术语表数据
  - 确保API请求的安全性和有效性
- **Acceptance Criteria Addressed**: AC-1, AC-3
- **Test Requirements**:
  - `programmatic` TR-5.1: 后端能正确接收和处理术语提取请求
  - `programmatic` TR-5.2: 后端能返回提取进度信息
  - `programmatic` TR-5.3: 提取的术语表能正确返回给前端
  - `programmatic` TR-5.4: 手动编辑后的术语表能正确应用
- **Notes**: 确保参数传递和处理的安全性

## [ ] Task 6: 测试和优化术语提取功能
- **Priority**: P2
- **Depends On**: Task 1, Task 2, Task 5
- **Description**:
  - 使用不同类型的PDF文档测试术语提取功能
  - 评估提取准确性并进行优化
  - 测试性能，确保提取过程不会影响用户体验
- **Acceptance Criteria Addressed**: AC-1, AC-4
- **Test Requirements**:
  - `programmatic` TR-6.1: 不同类型PDF的术语提取成功率
  - `programmatic` TR-6.2: 术语提取过程的响应时间
  - `human-judgement` TR-6.3: 提取术语的质量和相关性
- **Notes**: 可以使用现有的测试文档进行测试