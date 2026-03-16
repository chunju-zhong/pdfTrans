# PDF翻译工具 - 并行文本提取实现计划

## [x] Task 1: 修改GlossaryService类，创建按页提取文本的方法
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 创建一个新方法`_extract_page_text`，用于提取单个页面的文本
  - 该方法应接收PDF路径和页码作为参数，返回该页面的文本
- **Success Criteria**:
  - 新方法能够正确提取单个页面的文本
  - 方法参数和返回值符合预期
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证方法能够提取指定页面的文本
  - `programmatic` TR-1.2: 验证方法在页面不存在时返回空字符串
- **Notes**: 保持与现有`_extract_text_from_pdf`方法的兼容性

## [x] Task 2: 修改extract_glossary_from_pdf方法，实现并行文本提取和术语提取
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改`extract_glossary_from_pdf`方法，在线程池中并行执行文本提取和术语提取
  - 为每个页面提交一个任务，该任务先提取页面文本，然后提取术语
  - 等待所有任务完成并收集结果
- **Success Criteria**:
  - 方法能够并行处理文本提取和术语提取
  - 提取结果与原方法一致
  - 处理速度比原方法快
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证方法能够正确提取术语
  - `programmatic` TR-2.2: 比较修改前后的处理速度
- **Notes**: 注意线程安全，确保并发操作不会导致问题

## [x] Task 3: 测试和优化
- **Priority**: P1
- **Depends On**: Task 2
- **Description**: 
  - 测试不同大小PDF文件的处理性能
  - 优化线程池大小和任务分配策略
  - 确保在各种情况下的稳定性
- **Success Criteria**:
  - 处理速度比原方法快
  - 系统能够稳定处理各种情况
- **Test Requirements**:
  - `programmatic` TR-3.1: 测试大PDF文件的处理性能
  - `programmatic` TR-3.2: 测试边缘情况，如空PDF文件或只有一页的PDF文件
- **Notes**: 考虑不同系统配置的影响