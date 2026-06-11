# Tasks

- [ ] Task 1: 修复 `_add_similar_blocks` 函数，增加文本长度条件避免短文本误判
  - [ ] SubTask 1.1: 修改 `_add_similar_blocks` 函数，当两个文本块长度均<20字符时，仅当文本完全相同（相似度=100%）才标记为非正文
  - [ ] SubTask 1.2: 当一个文本块长度<20字符而另一个≥20字符时，使用相似度≥95%的阈值
  - [ ] SubTask 1.3: 当两个文本块长度均≥20字符时，保持当前相似度≥90%的阈值

# Task Dependencies

（无依赖关系）
