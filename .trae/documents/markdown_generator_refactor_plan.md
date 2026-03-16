# PDF翻译工具 - Markdown生成器重构 - 实现计划

## [/] Task 1: 将通用方法从AipingMarkdownGenerator移到MarkdownGenerator基类
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 将AipingMarkdownGenerator中实现的通用方法移到MarkdownGenerator基类
  - 包括：_convert_table_to_markdown、_copy_images_to_output、_process_pages、_process_page_elements、_add_image_to_markdown、_add_table_to_markdown、_find_chart_position、_find_merged_block、_process_chapter_pages、_generate_chapter_markdowns、_sanitize_filename、_generate_chapter_index
- **Success Criteria**:
  - MarkdownGenerator基类包含所有必要的方法
  - AipingMarkdownGenerator只包含aiping特定的代码
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证MarkdownGenerator基类包含所有必要的方法
  - `human-judgement` TR-1.2: 检查代码结构清晰，职责分明
- **Notes**: 确保所有方法都正确移动，保持方法签名和功能不变

## [ ] Task 2: 确保AipingMarkdownGenerator只保留aiping特定代码
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改AipingMarkdownGenerator类，只保留aiping特定的代码
  - 确保它正确继承MarkdownGenerator基类的所有方法
  - 只重写需要aiping特定处理的方法（如_call_api）
- **Success Criteria**:
  - AipingMarkdownGenerator只包含aiping特定的代码
  - 它正确继承并使用基类的所有方法
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证AipingMarkdownGenerator只包含aiping特定的代码
  - `human-judgement` TR-2.2: 检查AipingMarkdownGenerator的代码简洁清晰
- **Notes**: 确保AipingMarkdownGenerator的_call_api方法仍然正确添加extra_body参数

## [ ] Task 3: 测试修复效果
- **Priority**: P1
- **Depends On**: Task 1, Task 2
- **Description**: 
  - 运行系统处理PDF文档，分别使用aiping和silicon_flow API
  - 验证两种API都能正确生成Markdown文档
  - 检查生成的Markdown文件结构正确，包含所有必要的内容
- **Success Criteria**:
  - 使用aiping API能正确生成Markdown文档
  - 使用silicon_flow API能正确生成Markdown文档
  - 生成的Markdown文件结构正确，包含所有必要的内容
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证两种API都能成功生成Markdown文档
  - `human-judgement` TR-3.2: 检查生成的Markdown文件结构正确，内容完整
- **Notes**: 使用包含文本、表格和图像的测试文档进行验证