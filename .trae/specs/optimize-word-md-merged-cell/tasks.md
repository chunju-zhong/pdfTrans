# Tasks

- [x] Task 1: Word 表格合并单元格支持
  - [x] SubTask 1.1: 修改 `_add_table()` 读取 `row_span`/`col_span`，对合并单元格调用 `cell.merge()`
  - [x] SubTask 1.2: 跳过 `cell is None` 位置的文本写入
  - [x] SubTask 1.3: 设置合并单元格的字体大小（基于合并后高度）

- [x] Task 2: Markdown 表格合并单元格支持
  - [x] SubTask 2.1: 检测表格是否存在合并单元格
  - [x] SubTask 2.2: 有合并时使用 HTML `<table>` 格式输出，`<td>` 添加 `colspan`/`rowspan` 属性
  - [x] SubTask 2.3: 无合并时保持当前管道表格格式

- [x] Task 3: 验证
  - [x] SubTask 3.1: 语法检查通过
  - [x] SubTask 3.2: 运行现有测试无回归

# Task Dependencies

- Task 1 和 Task 2 可并行
- Task 3 依赖 Task 1 和 Task 2
