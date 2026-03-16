# 查找 PdfPage 等类的 copy 使用场景规格文档

## Why
分析代码中创建 PdfPage、TextBlock、MergedBlock 等类的新对象时，是否可以使用 copy() 方法来简化代码。

## 分析结果

### 1. PdfPage 类
在 `translation_service.py` 中有两处创建新的 PdfPage 对象：
- 第489行：`PdfPage(page_num, [])`
- 第654行：`PdfPage(page_num, [])`

这些是使用构造函数创建新对象，而不是复制现有对象。暂无使用 copy() 的场景。

### 2. TextBlock 类
在 `translation_service.py` 中有三处创建新的 TextBlock 对象：

**位置1** (第386-397行):
```python
translated_text_block = TextBlock(
    block_no=text_block.block_no,
    text=block_text,
    bbox=new_bbox,
    block_type=text_block.block_type,
    page_num=page_num
)
# 手动复制所有其他属性
for attr_name, attr_value in vars(text_block).items():
    if attr_name not in ['block_no', 'block_text', 'block_bbox', 'block_type', 'page_num']:
        setattr(translated_text_block, attr_name, attr_value)
```

**位置2** (第559-569行):
```python
translated_text_block = TextBlock(
    block_no=text_block.block_no,
    text=translated_text,
    bbox=text_block.block_bbox,
    block_type=text_block.block_type
)
# 手动复制所有其他属性
for attr_name, attr_value in vars(text_block).items():
    if attr_name not in ['block_no', 'block_text', 'block_bbox', 'block_type']:
        setattr(translated_text_block, attr_name, attr_value)
```

**优化建议**：可以使用 `text_block.copy()` 方法替代手动复制逻辑。

### 3. MergedBlock 类
在 `translation_service.py` 中有两处创建新的 MergedBlock 对象（第347行和第551行），都是使用构造函数创建新对象，暂无使用 copy() 的场景。

## What Changes
- 修改 `translation_service.py` 中 TextBlock 的创建逻辑，使用 `copy()` 方法简化代码

## Impact
- Affected code: `services/translation_service.py`

## ADDED Requirements

### Requirement: 使用 copy() 方法简化 TextBlock 创建
修改 translation_service.py 中 TextBlock 的创建逻辑。

#### Scenario: 使用 copy() 替代手动复制
- **GIVEN** 一个 TextBlock 对象 text_block
- **WHEN** 需要创建新的 TextBlock 对象并复制属性
- **THEN** 使用 `text_block.copy()` 方法，然后更新需要修改的属性
