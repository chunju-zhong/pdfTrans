## 问题分析

通过分析日志和代码，我发现了PDF翻译工具中文本块丢失的问题：

1. 从日志中可以看到，第8页的块21和块22都是正文块，但在合并过程中丢失了。
2. 问题出在`merge_semantic_blocks`函数中，当处理完所有块后，代码使用`elif`来检查`last_incomplete_sentence`。
3. 这意味着只有当`current_merged`为None时，函数才会检查`last_incomplete_sentence`是否存在。
4. 如果`current_merged`存在，函数会忽略`last_incomplete_sentence`，导致其中的原始块丢失。
5. 当处理非正文块时，正文块会被保存到`last_incomplete_sentence`中，而如果最后一个块是正文块，`current_merged`会存在，导致`last_incomplete_sentence`中的正文块丢失。

## 解决方案

修改`merge_semantic_blocks`函数，将处理`last_incomplete_sentence`的条件从`elif`改为`if`，这样无论`current_merged`是否存在，都会检查`last_incomplete_sentence`。

## 具体修改

1. 打开`/Users/chunju/work/pdfTrans/utils/text_processing.py`文件
2. 找到`merge_semantic_blocks`函数的最后部分（第205-211行）
3. 将第208行的`elif`改为`if`
4. 确保无论`current_merged`是否存在，都会检查并添加`last_incomplete_sentence`中的块

## 预期效果

修改后，当处理完所有块时，函数会：
1. 如果`current_merged`存在，将其添加到结果中
2. 无论`current_merged`是否存在，都会检查`last_incomplete_sentence`是否存在
3. 如果`last_incomplete_sentence`存在，将其添加到结果中
4. 这样可以确保所有原始块都被正确处理，不会丢失

## 测试计划

1. 运行现有的测试用例，确保修改不会破坏现有功能
2. 使用包含跨非正文块的正文块的PDF文件进行测试
3. 检查翻译结果，确保所有正文块都被正确翻译
4. 查看日志，确保所有正文块都被正确处理