# PDF翻译工具 - 章节Markdown生成问题修复计划

## 问题分析
根据日志分析，当按章节生成Markdown文件时，虽然系统检测到了9个章节，但是`chapter_content`为空，导致没有生成章节文件，只生成了章节索引文件。

```
2026-03-09 23:43:16,267 - modules.markdown_generator - INFO - 开始按章节组织内容，章节列表长度: 9
2026-03-09 23:43:16,267 - modules.markdown_generator - INFO - 章节内容组织完成，章节数量: 0
```

## 任务分解

### [/] 任务1: 检查文本块章节关联逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查`pdf_extractor.py`中的`_associate_chapters_with_blocks`方法
  - 确保它正确地为文本块关联章节信息
  - 检查`_find_block_chapter`方法的实现
- **Success Criteria**: 文本块能够正确关联到对应的章节
- **Test Requirements**:
  - `programmatic` TR-1.1: 文本块的`chapter_id`属性不为空
  - `programmatic` TR-1.2: 文本块的`chapter_title`属性不为空
- **Notes**: 重点检查`_find_block_chapter`方法的实现逻辑

### [ ] 任务2: 检查图像章节关联逻辑
- **Priority**: P1
- **Depends On**: Task 1
- **Description**: 
  - 检查是否有`_associate_chapters_with_images`方法
  - 如果没有，实现该方法
  - 确保图像能够正确关联到对应的章节
- **Success Criteria**: 图像能够正确关联到对应的章节
- **Test Requirements**:
  - `programmatic` TR-2.1: 图像的`chapter_id`属性不为空
  - `programmatic` TR-2.2: 图像的`chapter_title`属性不为空
- **Notes**: 图像的章节关联逻辑可能与文本块类似

### [ ] 任务3: 检查表格章节关联逻辑
- **Priority**: P1
- **Depends On**: Task 1
- **Description**: 
  - 检查是否有`_associate_chapters_with_tables`方法
  - 如果没有，实现该方法
  - 确保表格能够正确关联到对应的章节
- **Success Criteria**: 表格能够正确关联到对应的章节
- **Test Requirements**:
  - `programmatic` TR-3.1: 表格的`chapter_id`属性不为空
  - `programmatic` TR-3.2: 表格的`chapter_title`属性不为空
- **Notes**: 表格的章节关联逻辑可能与文本块类似

### [ ] 任务4: 改进章节内容组织逻辑
- **Priority**: P0
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 修改`_generate_chapter_markdowns`方法
  - 添加详细的日志，以便更好地诊断问题
  - 确保章节内容能够正确组织
- **Success Criteria**: 章节内容能够正确组织，`chapter_content`不为空
- **Test Requirements**:
  - `programmatic` TR-4.1: `chapter_content`的长度大于0
  - `programmatic` TR-4.2: 生成的章节文件数量与章节数量一致
- **Notes**: 添加详细的日志，以便更好地诊断问题

### [ ] 任务5: 测试章节Markdown生成功能
- **Priority**: P0
- **Depends On**: Task 4
- **Description**: 
  - 测试按章节生成Markdown文件的功能
  - 确保生成的章节文件数量与章节数量一致
  - 确保章节内容正确
- **Success Criteria**: 按章节生成Markdown文件功能正常
- **Test Requirements**:
  - `programmatic` TR-5.1: 生成的章节文件数量与章节数量一致
  - `human-judgement` TR-5.2: 章节文件内容正确，包含对应章节的文本、图像和表格
- **Notes**: 测试时使用包含多个章节的PDF文件

## 预期结果
- 系统能够正确检测PDF文档的章节结构
- 文本块、图像和表格能够正确关联到对应的章节
- 按章节生成Markdown文件时，能够生成与章节数量一致的章节文件
- 章节文件包含对应章节的文本、图像和表格
- 章节索引文件正确生成，包含所有章节的链接

## 风险评估
- **风险1**: 章节关联逻辑可能复杂，需要仔细测试
- **风险2**: 不同PDF文档的章节结构可能不同，需要考虑多种情况
- **风险3**: 图像和表格的章节关联可能需要特殊处理

## 实施步骤
1. 首先检查文本块章节关联逻辑
2. 然后检查图像和表格章节关联逻辑
3. 接着改进章节内容组织逻辑
4. 最后测试章节Markdown生成功能

## 时间估计
- 任务1: 1小时
- 任务2: 1小时
- 任务3: 1小时
- 任务4: 1小时
- 任务5: 1小时
- 总计: 5小时