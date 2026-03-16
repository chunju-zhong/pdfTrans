# PDF翻译工具 - 按章节拆分Markdown功能开关实现计划

## [ ] Task 1: 前端UI添加按章节拆分Markdown复选框
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 在前端表单中添加"按章节拆分Markdown"的复选框
  - 放置在输出格式选择附近，默认值为开启
  - 添加相应的提示文本说明功能
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `human-judgement` TR-1.1: 检查前端UI是否显示按章节拆分Markdown的复选框
  - `human-judgement` TR-1.2: 检查复选框是否默认开启
  - `human-judgement` TR-1.3: 检查是否有相应的功能说明文本

## [ ] Task 2: 修改后端路由接收按章节拆分参数
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 在Flask路由的translate函数中添加chapter_split参数
  - 确保参数能够正确传递给翻译服务
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 测试前端提交的chapter_split参数是否被正确接收
  - `programmatic` TR-2.2: 测试参数值是否正确传递给翻译服务

## [ ] Task 3: 修改翻译服务处理按章节拆分参数
- **Priority**: P0
- **Depends On**: Task 2
- **Description**:
  - 在TranslationService的process_translation方法中添加chapter_split参数
  - 将参数传递给extract_pdf_content和generate_output_files方法
  - 在extract_pdf_content方法中根据chapter_split参数决定是否提取章节信息
- **Acceptance Criteria Addressed**: AC-2, AC-3, AC-4, AC-5
- **Test Requirements**:
  - `programmatic` TR-3.1: 测试chapter_split参数是否正确传递到相关方法
  - `programmatic` TR-3.2: 测试参数值是否被正确处理
  - `programmatic` TR-3.3: 测试关闭按章节拆分时是否不执行章节提取分析

## [ ] Task 4: 修改generate_output_files方法处理按章节拆分逻辑
- **Priority**: P0
- **Depends On**: Task 3
- **Description**:
  - 在generate_output_files方法中添加chapter_split参数
  - 根据参数值决定是否按章节生成Markdown
  - 当chapter_split为True时，传递章节信息给Markdown生成器
  - 当chapter_split为False时，不传递章节信息，生成单一Markdown文件
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 测试选择按章节拆分时是否生成章节Markdown文件
  - `programmatic` TR-4.2: 测试不选择按章节拆分时是否生成单一Markdown文件
  - `programmatic` TR-4.3: 测试生成的文件是否符合预期格式

## [ ] Task 5: 测试功能完整性
- **Priority**: P1
- **Depends On**: Task 4
- **Description**:
  - 进行端到端测试，验证整个功能流程
  - 测试不同场景下的表现
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-5.1: 测试选择按章节拆分的完整流程
  - `programmatic` TR-5.2: 测试不选择按章节拆分的完整流程
  - `human-judgement` TR-5.3: 验证生成的文件质量和结构