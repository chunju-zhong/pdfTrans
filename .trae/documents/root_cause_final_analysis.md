# 文本块合并问题 - 根本原因分析（根据新日志）

## 关键发现

从最新的DEBUG日志中，找到了问题的根本原因！

## 详细分析

### 关键日志行

**L252 (i=1，处理块0 ↔ 块2):**
```
[DEBUG] 合并决策 i=1: should_merge=False, 
is_different_chapter=False, 
curr_chapter_id=chapter_0, 
current_chapter_id=chapter_0, 
is_chapter_title=True,  ← 这里！文本块2被错误标记为标题块！
current_is_title=False, 
can_merge=False, 
prev_block_text='Introduction to Agents and Age...', 
curr_block_text='Words are insufficient to desc...'
```

**L253 (i=1):**
```
[DEBUG] i=1: 结束当前合并块，原因: 当前块是标题，当前合并块不是标题
```
→ 结束块0，开始块2（被错误标记为标题）

**L254 (i=2，处理块2 ↔ 块3):**
```
[DEBUG] 合并决策 i=2: should_merge=True, 
is_different_chapter=False, 
curr_chapter_id=chapter_0, 
current_chapter_id=chapter_0, 
is_chapter_title=False, 
current_is_title=True,  ← 当前合并块（块2）被标记为标题
can_merge=True, 
prev_block_text='Words are insufficient to desc...', 
curr_block_text='anthropomorphize and use human...'
```

**L255 (i=2):**
```
[DEBUG] i=2: 结束当前合并块，原因: 当前块不是标题，当前合并块是标题
```
→ 结束块2，开始块3！

## 根本原因

**文本块2（"Words are insufficient to describe how humans interact with AI. We tend to"）被错误地标记为 `is_chapter_title=True`！**

这导致了连锁反应：
1. i=1时，块2被认为是标题块，所以结束块0，开始块2
2. i=2时，当前合并块（块2）被认为是标题，而当前块（块3）不是标题，所以又结束块2，开始块3
3. 最终，块2单独成为一个合并块，块3-6合并成另一个块

## 为什么文本块2被标记为标题块？

让我们查看章节标识符是如何标记`is_chapter_title`的。

在`modules/chapter_identifier.py:552-556`:
```python
title_block_nos = getattr(best_chapter, 'title_block_nos', [])
if title_block_nos and text_block.block_no in title_block_nos:
    text_block.is_title_block = True
else:
    text_block.is_title_block = False
```

问题在于：文本块2的`block_no=2`，而章节6的`title_block_nos=[2]`（从日志L31-32可以看到）！

从日志L31-32：
```
为标题 'From Predictive AI to Autonomous Agents' 找到最佳匹配: 类型=high_similarity, 位置=(72.0, 395.9997253417969), 块编号=[2]
```

所以章节6的标题块编号是`[2]`，而文本块2的`block_no=2`，所以它被错误地标记为标题块！

## 问题的根源

**块编号（block_no）是PDF原始块编号，而不是按Y坐标排序后的显示顺序编号！**

- 文本块2（显示顺序2）的`block_no=2`
- 章节6的标题块编号也是`[2]`
- 所以文本块2被错误地认为是章节6的标题块

但实际上：
- 章节6的标题在页面下方（y≈396）
- 文本块2在页面上方（y≈130）
- 它们虽然`block_no`相同，但位置完全不同！

## 解决方案

需要修改`is_title_block`的标记逻辑，除了检查`block_no`外，还要检查位置是否匹配！

或者，更好的方法是：在标记`is_title_block`时，不仅检查`block_no`，还要检查文本块的位置是否与章节标题的位置匹配。
