## 问题分析

在`translation_service.py`中，`all_blocks`列表将`TextBlock`对象转换为**字典格式**，增加了不必要的数据转换开销，并且导致了'dict' object has no attribute 'block\_text'错误。

**当前流程**：

1. `pdf_extractor`返回`PdfExtraction`对象，包含`PdfPage`列表
2. `PdfPage`对象包含`TextBlock`对象列表（已经按垂直位置排序）
3. 代码创建`all_blocks`字典列表，将`TextBlock`对象转换为字典
4. 调用`merge_semantic_blocks`函数处理字典列表，导致属性访问错误

## 解决方案

**优化方案**：直接使用`TextBlock`对象进行语义块合并，移除不必要的字典转换。

**具体步骤**：

1. 修改`merge_semantic_blocks`函数，使其能够直接处理`TextBlock`对象列表
2. 移除`translation_service.py`中创建`all_blocks`字典列表的代码
3. 直接从`extracted_content.pages`中收集`TextBlock`对象
4. 修改语义块合并后的处理逻辑，适应`TextBlock`对象的使用
5. 确保整个流程中数据类型一致，避免不必要的转换

## 修复步骤

1. **修改`merge_semantic_blocks`函数**：

   * 更新函数文档，说明支持`TextBlock`对象列表

   * 移除对字典格式的依赖，直接使用`TextBlock`对象属性

   * 确保合并后的块结构包含足够的信息供后续处理

2. **优化`translation_service.py`中的代码**：

   * 移除`all_blocks`字典列表的创建

   * 直接收集`TextBlock`对象和相关的页面信息

   * 修改合并块后的处理逻辑，直接使用`TextBlock`对象属性

3. **更新`split_translated_result`函数**：

   * 确保函数能够正确处理`TextBlock`对象列表

   * 简化逻辑，移除不必要的字典兼容代码

4. **测试修复效果**：

   * 验证语义块合并功能正常工作

   * 验证翻译流程能够顺利执行

   * 验证PDF生成功能正常工作

## 预期结果

* 修复'dict' object has no attribute 'block\_text'错误

* 简化代码流程，减少不必要的数据转换

* 提高代码的可读性和可维护性

* 减少类型转换导致的潜在错误

* 语义块合并和翻译功能正常工作

## 代码修改点

1. **文件**：`/Users/chunju/work/pdfTrans/utils/text_processing.py`

   * 函数：`merge_semantic_blocks`

   * 修改：适配`TextBlock`对象，移除字典依赖

2. **文件**：`/Users/chunju/work/pdfTrans/services/translation_service.py`

   * 代码段：110-128行（`all_blocks`创建）

   * 修改：直接使用`TextBlock`对象，移除字典转换

   * 代码段：133行（语义块合并调用）

   * 修改：传递`TextBlock`对象列表

   * 代码段：173-193行（翻译结果处理）

   * 修改：适应`TextBlock`对象的处理

## 优化后的流程

1. `pdf_extractor`返回`PdfExtraction`对象，包含`PdfPage`列表
2. 直接从`PdfPage`对象中收集`TextBlock`对象和页面信息
3. 调用`merge_semantic_blocks`函数处理`TextBlock`对象列表
4. 直接使用`TextBlock`对象属性进行翻译和结果处理
5. 简化数据流程，减少不必要的转换

## 预期代码结构

```python
# 移除all_blocks字典列表的创建
all_blocks = []
for page in extracted_content.pages:
    for text_block in page.text_blocks:
        all_blocks.append({
            # 字典转换代码...
        })

# 替换为直接收集TextBlock对象和页面信息
all_blocks_with_page_info = []
for page in extracted_content.pages:
    for text_block in page.text_blocks:
        all_blocks_with_page_info.append({
            'text_block': text_block,  # 直接保存TextBlock对象
            'page_num': page.page_num
        })
```

## 收益

* 简化代码流程，减少不必要的数据转换

* 避免类型转换导致的错误

* 提高代码的可读性和可维护性

* 减少内存占用和CPU开销

* 使代码更加一致，便于后续扩展和维护

