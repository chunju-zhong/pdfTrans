# 文本块合并问题 - 修复计划

## 问题分析

从日志L190-192可以看到：
```
文本块 block_no=2, title_block_nos=[2], is_title_block=True, 页码=8
```

**根本原因**：章节6的`title_block_nos=[2]`，但这个标题实际不在第8页！但是关联逻辑只检查了`text_block.block_no in title_block_nos`，没有检查章节的`page_num`是否与文本块的`page_num`匹配！

## 修复方案

修改 `associate_text_blocks` 方法，在检查 `text_block.block_no in title_block_nos` 的同时，还要检查 `best_chapter.page_num == text_block.page_num`。

## 实施步骤

### Task 1: 修改associate_text_blocks方法，增加页码检查
- **优先级**: P0
- **依赖**: 无
- **描述**: 
  - 在 `associate_text_blocks` 方法中
  - 检查 `title_block_nos` 的同时，检查章节的 `page_num` 是否与文本块的 `page_num` 相等
- **成功标准**: 
  - 只有当章节和文本块在同一页时，才会标记为标题块
- **测试要求**:
  - programmatic: 检查第8页的文本块2不再被标记为标题块
  - human-judgement: 验证日志中 is_title_block=False for block_no=2, page=8

### Task 2: 验证修复效果
- **优先级**: P1
- **依赖**: Task 1
- **描述**: 运行翻译，验证文本块2和3正确合并
- **成功标准**: 
  - 文本块2不再被标记为 `is_chapter_title=True`
  - 文本块2和3正确合并为一个块
- **测试要求**:
  - programmatic: 检查DEBUG日志中 `is_chapter_title=False` for i=1
  - human-judgement: 验证合并块内容包含原文2和3
