# 数据模型 Copy 机制抽象化 - 任务列表

## 任务列表

- [x] 任务1: 创建独立的 copyable.py 文件
  - [x] 在 models/ 目录下创建 copyable.py 文件
  - [x] 实现 CopyableMixin 类

- [x] 任务2: 修改 PdfTable 类继承 CopyableMixin
  - [x] 在 extraction.py 中导入 CopyableMixin
  - [x] 让 PdfTable 继承 CopyableMixin
  - [x] 移除现有的重复 copy() 方法

- [x] 任务3: 修改 PdfImage 类继承 CopyableMixin
  - [x] 让 PdfImage 继承 CopyableMixin
  - [x] 移除现有的重复 copy() 方法

- [x] 任务4: 测试验证
  - [x] 验证代码语法正确
