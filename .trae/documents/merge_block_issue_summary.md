# 文本块合并问题 - 根本原因分析和解决方案

## 问题概述

从日志观察到：
- 第8页文本块2（显示顺序）没有与文本块3合并
- LLM返回的合并决策为True，但实际没有合并

## 关键发现

### 1. 文本块14和15没有合并是正确的！
- LLM对这对的决策就是False（日志L243，决策数组索引13）
- 所以它们没有合并是符合预期的

### 2. 文本块2和3没有合并是问题所在
- LLM对这对的决策是True（日志L243，决策数组索引1）
- 但实际没有合并

## 根本原因

在`utils/text_processing.py`的`merge_semantic_blocks_with_llm_two_phase`函数中（L991-1017），除了LLM的`should_merge`决策外，还有**额外的条件检查**：

```python
# LLM决策
should_merge = merge_decisions[i-1]

# 额外条件检查
curr_chapter_id = getattr(curr_block, 'chapter_id', None)
is_different_chapter = curr_chapter_id != current_chapter_id
is_chapter_title = getattr(curr_block, 'is_title_block', False)
current_is_title = getattr(first_block_of_merged, 'is_title_block', False)

# 合并条件
can_merge = ((should_merge and not is_different_chapter) or
             (current_is_title and is_chapter_title and not is_different_chapter))

# 结束当前块的条件
should_end_current_block = False
if is_chapter_title and not current_is_title:
    should_end_current_block = True
elif not is_chapter_title and current_is_title:
    should_end_current_block = True
elif is_different_chapter:
    should_end_current_block = True
elif not can_merge:
    should_end_current_block = True
```

**最可能的问题**：虽然`is_different_chapter`、`is_chapter_title`或`current_is_title`中的某个条件被错误地判断，导致`should_end_current_block=True`，从而阻止了合并。

## 解决方案

### 方案1：添加详细调试日志（推荐首先实施）
在合并决策应用的地方添加详细日志，记录所有相关变量：

```python
logger.info(f"处理i={i}, should_merge={should_merge}, "
            f"is_different_chapter={is_different_chapter}, "
            f"curr_chapter_id={curr_chapter_id}, "
            f"current_chapter_id={current_chapter_id}, "
            f"is_chapter_title={is_chapter_title}, "
            f"current_is_title={current_is_title}, "
            f"can_merge={can_merge}, "
            f"should_end_current_block={should_end_current_block}")
```

### 方案2：调整合并条件优先级
修改合并逻辑，让LLM的决策有更高的权重：

```python
# 优先使用LLM决策，只有在明确的边界条件时才覆盖
should_end_current_block = False
if is_chapter_title and not current_is_title:
    should_end_current_block = True
elif not is_chapter_title and current_is_title:
    should_end_current_block = True
elif is_different_chapter:
    should_end_current_block = True
# 移除 elif not can_merge: 这一行，让LLM决策优先
```

或者简化can_merge条件，移除过于严格的检查：

```python
# 简化合并条件，主要依赖LLM决策
can_merge = should_merge or (current_is_title and is_chapter_title and not is_different_chapter)
```

### 方案3：验证章节和标题属性
确保`chapter_id`和`is_title_block`属性被正确设置：
- 检查章节ID的比较逻辑
- 检查标题块的检测逻辑
- 添加日志记录这些属性的值

## 建议的实施步骤

1. **首先实施方案1**：添加详细调试日志，重新运行，确认具体是哪个条件阻止了合并
2. **根据日志结果**，选择实施方案2或3来修复问题
3. **验证修复**：确保LLM的合并决策被正确应用

## 相关文件位置

- 合并逻辑：`/Users/chunju/work/pdfTrans/utils/text_processing.py:926-1060`
- 语义分析器：`/Users/chunju/work/pdfTrans/modules/semantic_analyzer.py`
- 章节识别：`/Users/chunju/work/pdfTrans/modules/chapter_identifier.py`
