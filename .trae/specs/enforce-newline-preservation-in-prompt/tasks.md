# Tasks

- [x] Task 1: 修改翻译提示词添加换行符保持规则
  - [x] SubTask 1.1: 在 `_generate_system_prompt` 方法中添加明确的换行符保持规则
  - [x] SubTask 1.2: 将规则编号调整为正确的顺序
  - [x] SubTask 1.3: 确保规则使用强调格式（加粗）提高大模型关注度

- [x] Task 2: 添加单元测试验证换行符保持
  - [x] SubTask 2.1: 创建测试用例验证单行文本翻译不添加换行符
  - [x] SubTask 2.2: 创建测试用例验证多行文本翻译保留换行符
  - [x] SubTask 2.3: 创建测试用例验证换行符数量一致性

# Task Dependencies

- [Task 2] depends on [Task 1]（测试需要先修改提示词）