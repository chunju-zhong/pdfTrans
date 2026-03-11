# PDF翻译工具 - 按章节生成Markdown功能实现计划

## [ ] 任务1: 实现基于书签的章节识别功能
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 使用PyMuPDF提取PDF文档的书签信息
  - 解析书签层级结构，构建章节树，限制章节嵌套最多3层
  - 为TextBlock添加章节信息属性，关联到对应的章节
  - 对没有明确章节结构的PDF文档，标记为不支持按章节生成Markdown
- **Acceptance Criteria Addressed**: AC-1, FR-5
- **Test Requirements**:
  - `programmatic` TR-1.1: 能够正确提取PDF文档中的书签信息
  - `programmatic` TR-1.2: 能够正确构建章节层级结构，限制最多3层
  - `programmatic` TR-1.3: 能够识别并提示不支持没有明确章节结构的PDF文档
- **Notes**: 使用PyMuPDF的bookmark功能来识别章节结构，章节嵌套最多支持3层

## [ ] 任务2: 扩展Markdown生成器支持章节拆分
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 修改MarkdownGenerator类，添加章节拆分功能
  - 实现按章节组织翻译内容的逻辑，支持嵌套层级拆分
  - 为每个章节（包括嵌套章节）生成单独的Markdown文件，最多拆分到第三层
  - 层级处理方案：
    - Level 1 Chapters: 生成Markdown文件，文件名为 "1. 章节标题.md" 格式
    - Level 2 Chapters: 生成Markdown文件，文件名为 "1.1. 章节标题.md" 格式
    - Level 3 Chapters: 生成Markdown文件，文件名为 "1.1.1. 章节标题.md" 格式
    - Levels Beyond 3: 不再进一步拆分，将内容合并到最近的Level 3章节中
- **Acceptance Criteria Addressed**: AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-2.1: 能够按章节组织翻译内容，支持嵌套层级
  - `programmatic` TR-2.2: 为每个章节生成单独的Markdown文件，最多拆分到第三层
  - `programmatic` TR-2.3: 正确处理嵌套层级，按照指定方案组织文件结构
- **Notes**: 需要保持与现有Markdown生成逻辑的兼容性，嵌套层级最多拆分到第三层

## [ ] 任务3: 生成章节索引文件
- **Priority**: P1
- **Depends On**: 任务2
- **Description**:
  - 实现章节索引文件的生成逻辑，支持嵌套层级
  - 为索引文件添加章节链接，保持层级结构
  - 确保索引文件的格式清晰易读，最多显示到第三层
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `human-judgment` TR-3.1: 索引文件包含所有章节的链接，保持层级结构
  - `human-judgment` TR-3.2: 索引文件格式清晰易读，最多显示到第三层
- **Notes**: 索引文件应该放在章节文件的同一目录下，保持嵌套层级结构

## [ ] 任务4: 集成到翻译服务流程
- **Priority**: P0
- **Depends On**: 任务2, 任务3
- **Description**:
  - 修改translation_service.py，集成章节识别和多Markdown文件生成功能
  - 确保与现有翻译流程的无缝集成
  - 添加相关的日志和错误处理
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 完整翻译流程能够正确处理章节识别和多Markdown文件生成
  - `programmatic` TR-4.2: 保持与现有功能的兼容性
- **Notes**: 需要确保不影响其他输出格式的生成

## [ ] 任务5: 测试和验证
- **Priority**: P1
- **Depends On**: 任务4
- **Description**:
  - 编写测试用例，验证章节识别功能
  - 测试多Markdown文件生成功能
  - 验证章节索引文件的生成
  - 确保与现有功能的兼容性
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-5.1: 所有测试用例通过
  - `human-judgment` TR-5.2: 生成的Markdown文件和索引文件符合预期
- **Notes**: 需要测试不同类型的PDF文档，包括有明确章节结构和没有章节结构的文档