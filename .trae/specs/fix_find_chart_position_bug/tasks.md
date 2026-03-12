# Bug修复任务: _find_chart_position收到合并块

## Task 1: 分析问题根源

- [x] 分析错误调用链
- [x] 确定问题原因：_process_chapter_pages传递了合并块而不是原始块

## Task 2: 修复_process_chapter_pages方法

- [x] 修改_process_chapter_pages方法
- [x] 提取合并块中的原始块列表
- [x] 将原始块列表传递给_process_page_elements
- 验证：图表定位使用原始块列表

## Task 3: 测试验证

- [x] 运行markdown_generator测试
- [x] 验证图表定位功能正常工作

## 测试结果
所有9个测试用例全部通过，修复成功！
