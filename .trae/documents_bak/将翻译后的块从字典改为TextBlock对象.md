## 实现计划：将翻译后的块从字典改为TextBlock对象，并将page_translated_blocks_dict改为使用PdfPage对象

### 1. 问题分析
- 当前翻译后的块使用字典格式创建和传递
- page_translated_blocks_dict使用字典格式存储页面级别的翻译结果
- 需要将两者都改为使用对象，提高代码的一致性和类型安全性

### 2. 实现步骤

#### 步骤1：修改translation_service.py

**修改点1：将创建翻译后的块字典改为创建TextBlock对象**
- **位置**：第178-189行
- **修改内容**：
  - 使用TextBlock构造函数创建对象，传入block_no、translated_text、block_bbox等参数
  - 更新样式信息
  - 将创建的TextBlock对象添加到翻译结果中

**修改点2：将page_translated_blocks_dict改为使用PdfPage对象**
- **位置**：第139-144行，第192行，第200行
- **修改内容**：
  - 导入PdfPage类
  - 将page_translated_blocks_dict的值从字典改为PdfPage对象
  - 将添加翻译块的代码改为添加到PdfPage对象的text_blocks列表中
  - 将构建translated_content['blocks']的代码改为使用PdfPage对象

#### 步骤2：修改pdf_generator.py

**修改点：将使用字典的代码改为使用对象属性访问**
- **位置**：_draw_translated_text_v2方法
- **具体修改点**：
  - 将`full_block['block_text']`改为`full_block.block_text`
  - 将`full_block['block_bbox']`改为`full_block.block_bbox`
  - 将`full_block.get('block_no', -1)`改为`full_block.block_no`
  - 其他使用`full_block['xxx']`的地方都改为`full_block.xxx`
  - 将`page_translated_blocks['blocks']`改为`page_translated_blocks.text_blocks`

#### 步骤3：验证修改
- 运行所有相关测试，确保修改后的代码能正常工作
- 检查是否有其他使用字典格式的地方需要修改
- 验证PDF生成是否正常，翻译文本是否完整输出

### 3. 预期效果
- 翻译后的块将使用TextBlock对象表示，提高代码的一致性和类型安全性
- 页面级别的翻译结果将使用PdfPage对象表示，简化代码结构
- PDF生成代码将直接使用对象的属性，避免了字典键名拼写错误的风险
- 提高了代码的可读性和可维护性

### 4. 具体实现细节

**translation_service.py修改**：
1. 在文件顶部导入PdfPage类
2. 将第141-144行改为：
   ```python
   page_translated_blocks_dict[page.page_num] = PdfPage(page.page_num, [])
   ```
3. 将第178-192行改为：
   ```python
   # 创建翻译后的TextBlock对象
   translated_text_block = TextBlock(
       block_no=text_block.block_no,
       text=block_text,
       bbox=text_block.block_bbox,
       block_type=text_block.block_type
   )
   # 更新样式信息
   translated_text_block.update_style(
       font=text_block.font,
       font_size=text_block.font_size,
       color=text_block.color,
       flags=text_block.flags
   )
   # 添加到对应页面的翻译结果中
   page_translated_blocks_dict[page_num].text_blocks.append(translated_text_block)
   ```
4. 将第200行改为：
   ```python
   translated_content['blocks'] = [page_translated_blocks_dict[page_num] for page_num in sorted(page_translated_blocks_dict.keys())]
   ```

**pdf_generator.py修改**：
1. 将第183行改为：
   ```python
   logger.info(f"开始绘制翻译文本V2，共 {len(translated_blocks.text_blocks)} 个完整文本块")
   ```
2. 将第186行改为：
   ```python
   for block_idx, full_block in enumerate(translated_blocks.text_blocks):
   ```
3. 将第190行改为：
   ```python
   translated_text = full_block.block_text
   ```
4. 将第194行改为：
   ```python
   block_bbox = full_block.block_bbox
   ```
5. 将第200行改为：
   ```python
   current_block_no = full_block.block_no
   ```

### 5. 测试计划
- 运行translation_service相关测试
- 运行pdf_generator相关测试
- 运行完整的PDF翻译测试
- 检查生成的PDF文件，确保翻译文本完整输出

### 6. 潜在风险和注意事项
- 确保所有相关代码都能正确处理TextBlock和PdfPage对象
- 注意TextBlock和PdfPage对象的属性名称，确保与当前字典键名对应
- 确保TextBlock和PdfPage对象的构造函数参数正确
- 运行全面的测试，确保修改不会引入新的问题

### 7. 依赖关系
- 依赖TextBlock类的正确实现
- 依赖PdfPage类的正确实现
- 依赖pdf_extractor模块生成的TextBlock对象

通过以上修改，我们将实现翻译后的块使用TextBlock对象，同时将page_translated_blocks_dict改为使用PdfPage对象，提高代码的一致性和可维护性。