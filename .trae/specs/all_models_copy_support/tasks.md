# 所有 Models 类增加 Copy 支持 - 任务列表

## 任务列表

- [x] 任务1: 修改 extraction.py
  - [x] PdfPage 继承 CopyableMixin
  - [x] PdfCell 继承 CopyableMixin
  - [x] PdfExtraction 继承 CopyableMixin

- [x] 任务2: 修改 text_block.py
  - [x] TextBlock 继承 CopyableMixin

- [x] 任务3: 修改 merged_block.py
  - [x] MergedBlock 继承 CopyableMixin

- [x] 任务4: 修改 task.py
  - [x] Task 继承 CopyableMixin

- [x] 任务5: 修改 result_types.py
  - [x] TruncationInfo 继承 CopyableMixin
  - [x] Result 继承 CopyableMixin

- [x] 任务6: 测试验证
  - [x] 验证所有类的 copy() 方法正常工作
