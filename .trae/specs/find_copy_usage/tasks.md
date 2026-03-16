# 查找 copy 使用场景 - 任务列表

## 任务列表

- [x] 任务1: 查找 TextBlock 手动复制属性的代码位置
  - [x] 分析 translation_service.py 中的 TextBlock 创建代码
  - [x] 发现两处手动复制属性的代码（第386-397行和第559-569行）

- [x] 任务2: 修改第一处 TextBlock 创建代码
  - [x] 使用 text_block.copy() 方法替代手动复制逻辑

- [x] 任务3: 修改第二处 TextBlock 创建代码
  - [x] 使用 text_block.copy() 方法替代手动复制逻辑

- [x] 任务4: 测试验证
  - [x] 验证代码语法正确
