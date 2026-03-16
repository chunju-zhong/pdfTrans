# 章节 9.7.1 表格丢失问题分析计划

## 问题描述
章节 9.7.1 应该包含一个表格（第36页），但实际输出显示"0图像, 0表格"。

## 日志分析

### 1. 表格正确归属到章节
```
2026-03-15 23:40:00,858 - modules.chapter_identifier - INFO - 表格 (页码: 36, y: 360.6752014160156) 归属于章节: 9.7.1 - Agent Identity: A New Class of Principal (章节位置: (72.0, 507.1298522949219))
```

### 2. 表格在翻译服务中被处理
```
2026-03-15 23:40:24,380 - services.translation_service - INFO - 任务 f6c22d69-f198-4bdb-868c-00bd17e46e7c 处理表格 0: 页码=36, 行数=4
```

### 3. 章节统计显示 0 表格
```
2026-03-15 23:40:26,592 - modules.markdown_generator - INFO - 章节 9.7.1 - Agent Identity: A New Class of Principal: 2页, 4文本块, 0图像, 0表格
```

## 根本原因分析

问题出在 `markdown_generator.py` 的 `_generate_chapter_markdowns` 方法中，表格添加到章节的逻辑有问题：

```python
# 组织表格
if 'tables' in translated_content:
    for table in translated_content['tables']:
        if table.chapter_id and table.chapter_id in chapter_content:
            # 添加表格到章节
```

关键问题：
1. 表格可能有 `chapter_id` 属性
2. 但 `chapter_content` 中存储的章节 ID 来自 `chapter.id`（如 `chapter_32`）
3. 表格的 `chapter_id` 可能与 `chapter.id` 不匹配

从日志可以看到：
- 章节列表中有 `chapter_32`
- 但没有看到 "表格添加到章节: chapter_32" 的日志

这说明表格的 `chapter_id` 与 `chapter.id` 不匹配，导致条件 `table.chapter_id in chapter_content` 为 False。

## 解决方案

需要检查并统一章节 ID 的生成逻辑，确保：
1. 文本块的 `chapter_id` 使用 `chapter.id`
2. 表格的 `chapter_id` 也使用 `chapter.id`
3. 或者在匹配时使用更灵活的匹配方式

具体修复步骤：
1. 在 `markdown_generator.py` 中添加调试日志，显示表格的 `chapter_id` 值
2. 检查翻译服务中表格的 `chapter_id` 是如何设置的
3. 确保表格的 `chapter_id` 与 `chapter.id` 一致
