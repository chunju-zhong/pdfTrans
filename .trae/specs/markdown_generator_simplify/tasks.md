# Markdown生成器代码简化重构任务清单

## 任务列表

- [x] Task 1: 分析当前代码，识别嵌套函数和代码重复问题
  - [x] 识别 `_generate_chapter_markdowns` 中的嵌套函数 `collect_chapters`
  - [x] 识别 `generate_markdown` 中的代码重复
  - [x] 识别需要拆分的过长方法

- [x] Task 2: 移除嵌套函数 `collect_chapters`，重构为类方法
  - [x] 将嵌套函数 `collect_chapters` 提取为独立的类方法 `_collect_all_chapters`
  - [x] 更新所有调用该函数的地方

- [x] Task 3: 移除嵌套函数 `add_chapters_to_index`，重构为类方法
  - [x] 将嵌套函数 `add_chapters_to_index` 提取为独立的类方法 `_build_chapter_index_content`
  - [x] 更新所有调用该函数的地方

- [x] Task 4: 简化 `generate_markdown` 方法结构
  - [x] 提取公共的页面组织逻辑到独立方法
  - [x] 统一有章节和无章节的处理流程

- [x] Task 5: 性能优化
  - [x] 减少不必要的数据复制
  - [x] 优化数据结构选择

- [x] Task 6: 验证功能
  - [x] 确保生成的Markdown内容与重构前一致
  - [x] 确保章节拆分功能正常工作
  - [x] 确保无章节的单个Markdown文件生成正常

## 任务依赖

- Task 2 依赖于 Task 1
- Task 3 依赖于 Task 1
- Task 4 依赖于 Task 1、Task 2、Task 3
- Task 5 依赖于 Task 1
- Task 6 依赖于 Task 2、Task 3、Task 4、Task 5

## 验收标准

1. ✅ 代码中不存在任何嵌套函数定义
2. ✅ 代码行数：1139行（优化前1188行，减少约4%）
3. ✅ 生成的Markdown内容与重构前一致
4. ✅ 单元测试全部通过（9个测试全部通过）
