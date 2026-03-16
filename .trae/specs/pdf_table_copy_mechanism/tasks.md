# PdfTable 对象 COPY 机制 - 任务列表

## 任务列表

- [x] 任务1: 在 PdfTable 类中添加 copy() 方法
  - [x] 分析 PdfTable 类的现有属性
  - [x] 实现 copy(exclude_attrs=None) 方法
  - [x] 确保方法正确复制所有实例属性

- [x] 任务2: 修改 _build_translated_tables 方法
  - [x] 使用 table.copy(exclude_attrs=['cells']) 创建翻译后的表格对象
  - [x] 更新 cells 属性为翻译后的内容
  - [x] 验证翻译后的表格包含原始的 chapter_id 等属性

- [x] 任务3: 为 PdfImage 类添加 COPY 机制
  - [x] 为 PdfImage 类添加 copy() 方法

- [x] 任务4: 测试验证
  - [x] 验证代码语法正确
