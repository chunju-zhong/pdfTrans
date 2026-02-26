# Markdown生成器调用更新计划

## [x] 任务1: 修改translation_service.py中的Markdown生成器调用
- **优先级**: P0
- **依赖关系**: None
- **描述**: 
  - 修改translation_service.py文件中的generate_markdown方法
  - 将直接创建MarkdownGenerator实例的代码替换为使用create_markdown_generator函数
  - 确保根据选择的翻译API类型自动使用相应的Markdown生成器
- **成功标准**: 
  - translation_service.py中的代码使用create_markdown_generator函数创建Markdown生成器实例
  - 代码能根据选择的翻译API类型正确选择相应的生成器
  - 所有测试通过
- **测试要求**: 
  - `programmatic` TR-1.1: 运行测试确保所有功能正常工作
  - `human-judgement` TR-1.2: 代码应清晰易读，符合项目的代码风格规范
- **注意事项**: 
  - 确保保持向后兼容性
  - 确保传递正确的参数给create_markdown_generator函数

## [x] 任务2: 测试修改后的代码
- **优先级**: P0
- **依赖关系**: 任务1
- **描述**: 
  - 运行测试套件确保修改后的代码正常工作
  - 验证不同翻译API类型的Markdown生成器都能正确创建和使用
- **成功标准**: 
  - 所有测试通过
  - 不同翻译API类型的Markdown生成器都能正确创建和使用
- **测试要求**: 
  - `programmatic` TR-2.1: 运行pytest测试套件
  - `programmatic` TR-2.2: 验证aiping和silicon_flow类型的生成器都能正确创建
- **注意事项**: 
  - 确保测试覆盖所有使用Markdown生成器的场景
  - 检查是否有任何边缘情况需要处理