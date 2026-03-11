# 优化章节信息传递 - 实现计划

## [ ] 任务1: 修改extract_pdf_content方法，直接返回章节信息
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 修改extract_pdf_content方法，在返回值中添加chapters信息
  - 从pdf_extractor中获取章节信息并包含在返回值中
- **Success Criteria**:
  - extract_pdf_content方法返回值包含chapters信息
  - 调用方可以直接使用返回的chapters信息
- **Test Requirements**:
  - `programmatic` TR-1.1: extract_pdf_content方法返回值包含chapters字段
  - `programmatic` TR-1.2: 章节信息正确提取和返回
- **Notes**: 需要确保向后兼容性，保持其他返回值不变

## [ ] 任务2: 修改process_translation方法，传递章节信息
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 修改process_translation方法，接收并传递chapters信息
  - 在调用generate_output_files时传递chapters参数
- **Success Criteria**:
  - process_translation方法正确处理chapters信息
  - 章节信息被正确传递给generate_output_files方法
- **Test Requirements**:
  - `programmatic` TR-2.1: process_translation方法正确接收chapters信息
  - `programmatic` TR-2.2: 章节信息被正确传递给generate_output_files
- **Notes**: 需要更新方法调用和参数传递

## [ ] 任务3: 修改generate_output_files方法，使用章节信息
- **Priority**: P0
- **Depends On**: 任务2
- **Description**:
  - 修改generate_output_files方法，接收chapters参数
  - 不再从pdf_extractor获取章节信息，而是直接使用传入的chapters
- **Success Criteria**:
  - generate_output_files方法正确接收和使用chapters参数
  - Markdown生成器能够正确处理传入的chapters信息
- **Test Requirements**:
  - `programmatic` TR-3.1: generate_output_files方法正确接收chapters参数
  - `programmatic` TR-3.2: Markdown生成器使用传入的chapters信息
- **Notes**: 需要更新方法签名和内部逻辑

## [ ] 任务4: 测试和验证
- **Priority**: P1
- **Depends On**: 任务3
- **Description**:
  - 运行所有测试用例，确保修改后的代码正常工作
  - 验证章节信息传递和Markdown生成功能
- **Success Criteria**:
  - 所有测试用例通过
  - 按章节生成Markdown功能正常工作
- **Test Requirements**:
  - `programmatic` TR-4.1: 所有测试用例通过
  - `human-judgment` TR-4.2: 按章节生成的Markdown文件符合预期
- **Notes**: 需要测试有章节和无章节的情况