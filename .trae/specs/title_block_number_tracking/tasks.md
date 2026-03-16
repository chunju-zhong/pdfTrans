# Tasks
- [x] Task 1: 修改 Chapter 类，添加 title_block_nos 属性
  - [x] SubTask 1.1: 在 Chapter 类中添加 title_block_nos 属性
- [x] Task 2: 修改 _find_title_position 方法，返回块编号列表
  - [x] SubTask 2.1: 修改方法返回值为 (position, block_nos) 元组
  - [x] SubTask 2.2: 在跨块匹配时记录连续块编号列表
  - [x] SubTask 2.3: 添加 flags=1 参数保持与PDF提取一致
- [x] Task 3: 修改章节创建逻辑，保存标题块编号列表
  - [x] SubTask 3.1: 修改 _build_chapter_tree 中调用 _find_title_position 的代码
  - [x] SubTask 3.2: 将 block_nos 保存到 Chapter 对象
- [x] Task 4: 修改章节分配逻辑，设置 is_title_block 属性
  - [x] SubTask 4.1: 在章节分配方法中获取 title_block_nos
  - [x] SubTask 4.2: 为标题块设置 is_title_block = True
- [x] Task 5: 修改语义合并逻辑（第102-105行附近）
  - [x] SubTask 5.1: 将文本匹配改为使用 is_title_block 属性
- [x] Task 6: 修改语义合并逻辑（第1009-1017行附近）
  - [x] SubTask 6.1: 将文本匹配改为使用 is_title_block 属性
- [ ] Task 7: 测试验证
  - [ ] SubTask 7.1: 使用包含长标题的PDF进行测试
  - [ ] SubTask 7.2: 验证标题块正确识别和合并

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 3]
- [Task 5] depends on [Task 4]
- [Task 6] depends on [Task 4]
- [Task 7] depends on [Task 5, Task 6]
