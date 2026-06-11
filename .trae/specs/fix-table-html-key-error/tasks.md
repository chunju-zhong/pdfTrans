# Tasks

- [x] Task 1: 步骤1启用表格识别
  - [x] SubTask 1.1: 在 `extract_pdf` 方法中，将步骤1的 `_create_pipeline(use_table=False, ...)` 改为 `_create_pipeline(use_table=not self._skip_table, ...)`
- [x] Task 2: 步骤1处理表格识别结果
  - [x] SubTask 2.1: 在步骤1的 `result` 处理循环中，从 `result.get("table_res_list", [])` 提取表格结果
  - [x] SubTask 2.2: 从 `table_res.html` 中使用键名 `'pred'` 提取 HTML（`html_dict.get('pred', '')`）
  - [x] SubTask 2.3: 从 `parsing_res_list` 中提取 `label == 'table'` 的 bbox 作为表格位置
  - [x] SubTask 2.4: 创建 `PdfTable` 对象并添加到结果中
  - [x] SubTask 2.5: 增加表格识别诊断日志（`table_res_list` 长度、HTML 提取结果）
- [x] Task 3: 移除步骤2
  - [x] SubTask 3.1: 移除 `_process_page_tables` 方法
  - [x] SubTask 3.2: 移除步骤2的管线创建和调用逻辑
  - [x] SubTask 3.3: 移除步骤2相关的内存管理和管线释放代码
- [x] Task 4: 更新步骤1返回值
  - [x] SubTask 4.1: 步骤1返回值中增加 `tables` 字段（`PdfTable` 列表）
  - [x] SubTask 4.2: 移除 `has_table` 字段（不再需要，直接通过 `tables` 列表判断）

# Task Dependencies

- Task 2 依赖 Task 1（需要步骤1启用表格识别才有 `table_res_list`）
- Task 3 依赖 Task 2（步骤1处理表格后才能移除步骤2）
- Task 4 依赖 Task 2（返回值格式变更）
