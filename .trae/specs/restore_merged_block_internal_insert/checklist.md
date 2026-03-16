# 恢复合并块内部图表插入功能 - 检查清单

## 实现检查

- [x] **检查点1**: docx_generator.py 中的 _process_page_elements 方法已修改，增加了检测图表是否位于合并块内部的逻辑
- [x] **检查点2**: docx_generator.py 中当图表位于合并块内部时，调用 _insert_element_in_text_block 方法
- [x] **检查点3**: markdown_generator.py 中的 _process_page_elements 方法已修改，增加了检测图表是否位于合并块内部的逻辑
- [x] **检查点4**: markdown_generator.py 中创建了 _insert_element_in_merged_block 辅助方法
- [x] **检查点5**: markdown_generator.py 中当图表位于合并块内部时，正确拆分文本并插入图表
- [x] **检查点6**: 按章节生成Markdown时也应用了相同的内部插入逻辑（通过调用 _process_page_elements 自动实现）

## 功能验证检查

- [x] **检查点7**: Word生成器能正确处理图表位于合并块内部的情况
- [x] **检查点8**: Markdown生成器（完整模式）能正确处理图表位于合并块内部的情况
- [x] **检查点9**: Markdown生成器（章节模式）能正确处理图表位于合并块内部的情况
- [x] **检查点10**: 当图表位于合并块外部时，现有的在合并块之前/之后插入的逻辑仍然正常工作

## 代码质量检查

- [x] **检查点11**: 代码遵循项目的代码风格规范
- [x] **检查点12**: 关键方法有适当的文档字符串
- [x] **检查点13**: 添加了必要的调试日志
