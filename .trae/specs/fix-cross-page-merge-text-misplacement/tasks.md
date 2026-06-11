# Tasks

- [x] Task 1: 在 `identify_page_numbers()` 中增加罗马数字页码识别
  - [x] SubTask 1.1: 添加罗马数字正则表达式 `ROMAN_NUMERAL_PATTERN`，匹配独立罗马数字（i-xlix 范围）
  - [x] SubTask 1.2: 添加罗马数字转阿拉伯数字的辅助函数 `roman_to_int()`
  - [x] SubTask 1.3: 在 `identify_page_numbers()` 中增加罗马数字检测逻辑：遍历所有文本块，检测顶部/底部15%区域的独立罗马数字，字体较小（< 10.0），添加到 `page_number_set`
  - [x] SubTask 1.4: 添加罗马数字页码识别的日志记录

- [x] Task 2: 添加罗马数字页码识别的单元测试
  - [x] SubTask 2.1: 测试独立罗马数字（"xv"、"xii"、"iii"）被识别为页码
  - [x] SubTask 2.2: 测试非独立罗马数字（"Part III"、"Chapter IV"）不被识别
  - [x] SubTask 2.3: 测试罗马数字与阿拉伯数字混合编号场景
  - [x] SubTask 2.4: 测试 `roman_to_int()` 转换函数

- [x] Task 3: 验证修复效果
  - [x] SubTask 3.1: 运行现有测试确保无回归
  - [x] SubTask 3.2: 检查页码识别日志确认罗马数字被正确识别

# Task Dependencies

- Task 2 依赖 Task 1 完成
- Task 3 依赖 Task 1、2 全部完成
