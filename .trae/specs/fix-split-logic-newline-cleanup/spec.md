# 修复拆分逻辑未清理标题换行符导致新问题 Spec

## Why

修改文本提取逻辑清理换行符后，出现了新问题："2.4. 1 一般场地"标题换行了。根因是翻译API返回的结果包含换行符，但拆分逻辑（`split_translated_result`）未清理标题类文本的换行符。

## 根因分析

### 问题链

从日志分析：

1. **原文提取时已清理换行符**（第151-158行）：
   ```
   [换行符清理] 标题文本清理换行符: '2.4.1 General Sites \n' -> '2.4.1 General Sites'
   ```
   ✓ 提取阶段清理成功

2. **翻译API返回结果包含换行符**（第873-874行）：
   ```
   合并翻译结果: "2.4 地质勘察范围 2.4.1 一般场地\n地质勘察的范围取决于..."
   ```
   ✗ 翻译API返回了换行符

3. **拆分逻辑未清理换行符**（第898-900行）：
   ```
   块 3: 长度=240, 内容='1 一般场地\n地质勘察的范围取决于...'
   ```
   ✗ 拆分后的块包含换行符

### 原始块分析

从日志第877-879行：
```
合并块 4 原始块 1: '2.4 EXTENT OF GROUND INVESTIGATION...' (字体=12.0)
合并块 4 原始块 2: '2.4.1 General Sites...' (字体=12.0)
合并块 4 原始块 3: 'The extent of a ground investigation...' (字体=12.0)
```

拆分结果（第900行）：
```
['2.4 地质勘察范围', '2.4.', '1 一般场地\n地质勘察的范围取决于...']
```

**问题**：块1和块2是标题，但拆分后块3包含了换行符 `\n`。

### 根本原因

**拆分逻辑未识别标题块并清理换行符**：
- `split_translated_result` 函数按长度比例拆分，不识别标题
- 拆分后的标题文本包含换行符，导致渲染时换行

## What Changes

- **在拆分逻辑中清理标题类文本的换行符**：识别标题块（根据原始块特征），清理换行符
- **标题识别逻辑**：根据原始块的字体大小、文本内容（章节号）判断是否是标题
- **清理策略**：将 `\n` 替换为空格，清理多余空格

## Impact

- Affected code: `utils/text_processing.py` 的 `split_translated_result` 函数
- 行为变更：拆分后的标题文本会清理换行符
- 影响范围：所有合并翻译结果的拆分

## ADDED Requirements

### Requirement: 拆分逻辑清理标题类文本的换行符

系统 SHALL 在拆分翻译结果时，识别标题块并清理换行符。

#### Scenario: 识别标题块

- **WHEN** 拆分翻译结果
- **THEN** 根据原始块特征判断是否是标题：
  - 字体大小 > 14pt
  - 文本包含章节号（如 "2.4"、"2.4.1"、"Chapter 1"）
  - 文本较短（< 100字符）

#### Scenario: 清理标题块的换行符

- **WHEN** 拆分后的块被识别为标题
- **THEN** 清理换行符：`text.replace('\n', ' ')`
- **AND** 清理多余空格：`' '.join(text.split())`
- **AND** 记录清理日志

#### Scenario: 正文块保留换行符

- **WHEN** 拆分后的块不是标题
- **THEN** 保留换行符（正文可能需要多行）

## MODIFIED Requirements

### Requirement: 修改 split_translated_result 函数

修改 `utils/text_processing.py` 的 `split_translated_result` 函数，在拆分后清理标题类文本的换行符：

修改位置：第561行附近（分配文本后）

修改前：
```python
translated_blocks[i] = current_text
logger.info(f"块 {i+1}: 分配文本='{current_text[:100]}...' (长度={len(current_text)})")
```

修改后：
```python
# 判断是否是标题并清理换行符
original_block = original_blocks[i]
if _is_title_block(original_block, current_text):
    # 清理标题文本的换行符
    original_current_text = current_text
    current_text = current_text.replace('\n', ' ')
    current_text = ' '.join(current_text.split())
    if '\n' in original_current_text:
        logger.info(f"[拆分换行符清理] 标题文本清理换行符: '{original_current_text[:30]}' -> '{current_text[:30]}'")

translated_blocks[i] = current_text
logger.info(f"块 {i+1}: 分配文本='{current_text[:100]}...' (长度={len(current_text)})")
```

### Requirement: 添加标题识别函数

添加 `_is_title_block` 函数，判断原始块是否是标题：

```python
def _is_title_block(original_block, translated_text):
    """判断原始块是否是标题
    
    Args:
        original_block: 原始块对象（TextBlock）
        translated_text: 拆分后的翻译文本
        
    Returns:
        bool: 是否是标题
    """
    # 获取字体大小
    font_size = getattr(original_block, 'font_size', 0)
    
    # 获取原始文本
    original_text = getattr(original_block, 'block_text', '')
    
    # 标题判断条件：
    # 1. 字体大小较大（> 14pt）
    # 2. 文本较短（< 100字符）
    # 3. 包含章节号（如 "2.4"、"2.4.1"、"Chapter 1"）
    
    is_large_font = font_size > 14.0
    is_short_text = len(translated_text.strip()) < 100
    has_chapter_number = any(
        re.match(pattern, original_text.strip())
        for pattern in [
            r'^\d+\.\d+',  # 如 2.4, 2.4.1
            r'^Chapter\s+\d+',  # 如 Chapter 1
            r'^第[一二三四五六七八九十\d]+[章节]',  # 如 第一章, 第2节
        ]
    )
    
    # 判断逻辑：满足以下任一条件即为标题
    is_title = (
        (is_large_font and is_short_text) or
        has_chapter_number
    )
    
    return is_title
```

## REMOVED Requirements

（无移除的需求）