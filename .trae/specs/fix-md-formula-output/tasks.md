# Tasks

- [x] Task 1: 在布局格式化系统提示词中增加公式保护规则
  - [x] SubTask 1.1: 在 `_load_layout_prompt()` 的 B. 最终输出规范中添加第 6 条规则，要求保留 `$...$` 和 `$$...$$` 公式标记，不修改公式内容，包含正确/错误示例

- [x] Task 2: 区分行内公式与独立行公式，使用不同的包裹符号
  - [x] SubTask 2.1: 在 `_process_page_elements()` 中，根据公式块 bbox 宽度占页面宽度的比例判断行内/独立行，分别使用 `$...$` 和 `$$...$$`
  - [x] SubTask 2.2: 在 `_insert_element_in_merged_block()` 中，同样区分行内/独立行公式

# Task Dependencies

- [Task 1] 和 [Task 2] 互相独立，可并行执行
