# 文本块合并问题 - 根本原因分析和解决方案计划

## 问题描述

文本块2（显示顺序）被错误地标记为标题块，导致与文本块3没有合并。

## 根本原因分析

### 关键发现

**章节标题识别的** **`title_block_nos`** **存储的是"当前页的块提取顺序编号"，而** **`associate_text_blocks`** **传入的是"需要翻译的所有页的所有文本按页拼接后的显示顺序编号"！**

### 问题流程详解

1. **标题识别阶段**（`_find_title_position`）：

   * PyMuPDF返回的blocks是按提取顺序的（不是按Y轴排序的显示顺序）

   * 代码中使用 `i` 作为块编号，这是提取顺序而非 `block_no`

2. **文本块提取阶段**（`pdf_extractor.py`）：

   * 文本块按Y坐标排序后创建 `TextBlock` 对象

   * `TextBlock.block_no` 是原始提取时的编号

3. **章节关联阶段**（`associate_text_blocks`）：

   * 比较 `text_block.block_no` 与 `title_block_nos`

   * 但两者使用的编号体系不同！

## 解决方案

### 核心思路

**修改** **`_find_title_position`** **方法**：文本提取完成后，先按Y轴排序为显示顺序，然后再进行判断，并且记录的是块号 `block_no`，而不是提取顺序 `i`。

关键点：

* blocks\[i]\[5] 返回的是原始块编号（PyMuPDF的block\_no）

* 排序后使用enumerate获取显示顺序，但记录时使用原始块编号

* 跨块合并时，直接从排序后的块对象中提取原始块编号

### 具体修改

#### 修改1：\_find\_title\_position 方法

**位置**：`/Users/chunju/work/pdfTrans/modules/chapter_identifier.py#L222-223`

**当前代码逻辑**：

```python
page = doc[page_num - 1]
blocks = page.get_text('blocks', flags=1)

for i in range(len(blocks)):
    # ...
    block_nos = [i]  # 使用的是提取顺序索引
    # ...
    block_nos = list(range(i, i + j + 1))  # 跨块合并时的编号
```

**修改为**：

```python
page = doc[page_num - 1]
blocks = page.get_text('blocks', flags=1)

# 按Y坐标（blocks[i][1]）排序，获取显示顺序
# 每个block的第6个元素(索引5)是原始块编号
sorted_blocks = sorted(blocks, key=lambda x: x[1])  # 按y0排序

for display_order, block in enumerate(sorted_blocks):
    original_block_no = block[5]  # 原始块编号
    
    # 单块匹配
    block_nos = [original_block_no]  # 使用原始块编号！
    
    # 跨块匹配时，从排序后的块对象中提取原始块编号
    for j in range(min(3, len(sorted_blocks) - display_order)):
        merged_blocks = sorted_blocks[display_order:display_order + j + 1]
        block_nos = [b[5] for b in merged_blocks]  # 直接提取原始块编号！
        # ...
```

**代码解释**：

1. `sorted_blocks = sorted(blocks, key=lambda x: x[1])`：

   * PyMuPDF的`get_text('blocks')`返回的blocks是按原始提取顺序的

   * 我们按Y坐标（索引1）排序，得到显示顺序

   * `blocks`中的每个元素是一个元组，索引5是原始块编号block\_no

2. `for display_order, block in enumerate(sorted_blocks)`：

   * `display_order`是排序后的显示顺序（0, 1, 2, ...）

   * `block`是排序后的块对象

3. `original_block_no = block[5]`：

   * 从排序后的块对象中提取原始块编号

   * 这与`TextBlock.block_no`使用的编号体系一致

4. `merged_blocks = sorted_blocks[display_order:display_order + j + 1]`：

   * 当检测到跨块匹配时（如标题文本分散在多个块中）

   * 从当前显示顺序位置开始，取j+1个块

   * 例如：j=0时取1个块，j=1时取2个块，j=2时取3个块

5. `block_nos = [b[5] for b in merged_blocks]`：

   * 从合并的多个块中提取各自的原始块编号

   * 使用列表推导式简洁地获取所有原始块编号

   * 例如：如果merged\_blocks包含3个块，则block\_nos可能是\[2, 3, 4]

**为什么要这样改**：

* 原来使用`range(i, i + j + 1)`假设原始块编号是连续的

* 但实际上PyMuPDF的原始块编号可能不连续

* 使用`b[5]`直接从每个块对象中提取原始块编号更加准确

* 这样记录下来的`title_block_nos`与`TextBlock.block_no`使用的编号体系一致

#### 修改2：\_process\_page 方法

**位置**：`modules/pdf_extractor.py` 的 `_process_page` 方法

在文本块按Y坐标排序后、创建PdfPage对象之前，调用章节关联：

```python
# 按垂直位置排序TextBlock对象
sorted_text_blocks = sorted(
    text_block_objects.values(),
    key=lambda block: block.block_bbox[1]
)

# 添加章节关联！
if self.chapter_identifier.has_chapters():
    self.chapter_identifier.associate_text_blocks(sorted_text_blocks)

# 创建PdfPage对象
pdf_page = PdfPage(
    page_num=current_page_num,
    text_blocks=sorted_text_blocks
)
```

#### 修改3：extract 方法

**位置**：`modules/pdf_extractor.py` 的 `extract` 方法

移除所有文本块的统一关联代码：

```python
# 移除文本块的统一关联（因为已经在_process_page中按页关联了）
# 保留表格和图像的统一关联
if self.chapter_identifier.has_chapters():
    if extraction_result.tables:
        self.chapter_identifier.associate_tables(extraction_result.tables)
    if extraction_result.images:
        self.chapter_identifier.associate_images(extraction_result.images)
```

## 实施步骤

### Task 1: 修改\_find\_title\_position方法，使用block\_no记录

* **优先级**: P0

* **依赖**: 无

* **描述**:

  * 在 `_find_title_position` 方法中，blocks按Y坐标排序

  * 使用原始提取编号 `block_no`（即 block\[5]）作为 `block_nos`

  * 跨块合并时，直接从排序后的块对象中提取原始块编号

* **成功标准**:

  * `title_block_nos` 中存储的是原始块编号 `block_no`

  * 与 `TextBlock.block_no` 一致

* **测试要求**:

  * `programmatic`: 检查章节的 `title_block_nos` 使用正确的编号

### Task 2: 修改\_process\_page方法，添加章节关联

* **优先级**: P0

* **依赖**: Task 1

* **描述**:

  * 在 `_process_page` 方法中，文本块按Y坐标排序后、创建PdfPage对象之前

  * 调用 `self.chapter_identifier.associate_text_blocks(sorted_text_blocks)`

* **成功标准**:

  * 每页提取完成后，文本块立即被关联到对应章节

  * 块编号在该页内是正确的索引

* **测试要求**:

  * `programmatic`: 检查每页的文本块都有正确的chapter\_id和is\_title\_block属性

  * `human-judgement`: 验证日志中不再出现误判的标题块

### Task 3: 修改extract方法，移除文本块的统一关联

* **优先级**: P0

* **依赖**: Task 2

* **描述**:

  * 移除extract方法中所有文本块的统一关联代码

  * 保留表格和图像的统一关联

* **成功标准**: 代码不再对所有页的文本块进行统一关联

* **测试要求**: 功能不受影响

### Task 4: 验证修复效果

* **优先级**: P1

* **依赖**: Task 1, Task 2, Task 3

* **描述**: 运行翻译，验证文本块2和3正确合并

* **成功标准**:

  * 文本块2不再被标记为 `is_chapter_title=True`

  * 文本块2和3正确合并为一个块

* **测试要求**:

  * `programmatic`: 检查DEBUG日志中 `is_chapter_title=False` for i=1

  * `human-judgement`: 验证合并块内容包含原文2和3

