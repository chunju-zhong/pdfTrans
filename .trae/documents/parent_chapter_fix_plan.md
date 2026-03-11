# PDF翻译工具 - 父章节不包含子章节内容 - 实现计划

## [x] Task 1: 移除文本块添加到父章节的逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 修改 `modules/markdown_generator.py` 文件中的 `_generate_chapter_markdowns` 方法
  - 移除将文本块添加到父章节的代码（第940-955行）
- **Success Criteria**:
  - 文本块不再被添加到父章节中
  - 每个文本块只属于其直接所属的章节
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证文本块只被添加到其直接所属的章节
  - `human-judgement` TR-1.2: 检查生成的Markdown文件中父章节不包含子章节的内容
- **Notes**: 只修改文本块的处理逻辑，保持其他逻辑不变

## [x] Task 2: 移除图像添加到父章节的逻辑
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改 `modules/markdown_generator.py` 文件中的 `_generate_chapter_markdowns` 方法
  - 移除将图像添加到父章节的代码（第971-986行）
- **Success Criteria**:
  - 图像不再被添加到父章节中
  - 每个图像只属于其直接所属的章节
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证图像只被添加到其直接所属的章节
  - `human-judgement` TR-2.2: 检查生成的Markdown文件中父章节不包含子章节的图像
- **Notes**: 只修改图像的处理逻辑，保持其他逻辑不变

## [x] Task 3: 移除表格添加到父章节的逻辑
- **Priority**: P0
- **Depends On**: Task 1, Task 2
- **Description**: 
  - 修改 `modules/markdown_generator.py` 文件中的 `_generate_chapter_markdowns` 方法
  - 移除将表格添加到父章节的代码（第1001-1016行）
- **Success Criteria**:
  - 表格不再被添加到父章节中
  - 每个表格只属于其直接所属的章节
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证表格只被添加到其直接所属的章节
  - `human-judgement` TR-3.2: 检查生成的Markdown文件中父章节不包含子章节的表格
- **Notes**: 只修改表格的处理逻辑，保持其他逻辑不变

## [x] Task 4: 测试修复效果
- **Priority**: P1
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 运行系统处理包含父子章节结构的PDF文档
  - 验证生成的Markdown文件中父章节不包含子章节的内容
  - 检查系统其他功能是否正常运行
- **Success Criteria**:
  - 父章节只包含其直接内容，不包含子章节的内容
  - 子章节的内容只出现在子章节的Markdown文件中
  - 系统其他功能正常运行
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证父章节的Markdown文件不包含子章节的内容
  - `human-judgement` TR-4.2: 检查生成的Markdown文件结构正确，父子章节内容分离
- **Notes**: 使用包含多级章节结构的测试文档进行验证