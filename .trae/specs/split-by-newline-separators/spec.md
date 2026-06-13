# 拆分时以换行符为分隔点 Spec

## Why

当前拆分算法按比例分配翻译文本，不考虑换行符位置。导致换行符被分配到不应该包含换行符的文本块，引发文本框溢出和截断问题。

例如第15页的问题：
- 原文是两个独立的单行文本块（文本块3和文本块4）
- 合并翻译后包含换行符
- 拆分时换行符被分配到文本块3（高度16.3像素，单行）
- 导致文本块3渲染时溢出，被截断

## What Changes

- **以换行符为分隔点拆分**：当翻译结果包含换行符时，优先以换行符为分隔点拆分
- **匹配原始块数量**：确保拆分后的块数量与原始块数量一致
- **处理不匹配情况**：当换行符数量与原始块数量不匹配时，采用混合策略

## Impact

- Affected code: `utils/text_processing.py` 的 `split_translated_result` 函数（第431-688行）
- 行为变更：拆分算法优先以换行符为分隔点
- 影响范围：所有合并翻译结果的拆分

## ADDED Requirements

### Requirement: 拆分算法优先以换行符为分隔点

系统 SHALL 在拆分翻译结果时，优先以换行符为分隔点，将多行文本正确分配到对应的原始文本块。

#### Scenario: 换行符数量与原始块数量匹配

- **WHEN** 翻译结果包含 N 个换行符
- **AND** 原始块数量为 N+1
- **THEN** 以换行符为分隔点拆分，每个块对应一行翻译文本
- **AND** 拆分后的块数量与原始块数量一致

#### Scenario: 换行符数量少于原始块数量

- **WHEN** 翻译结果包含 M 个换行符
- **AND** 原始块数量为 N（M < N-1）
- **THEN** 先以换行符拆分，得到 M+1 个块
- **AND** 将剩余的 N-M-1 个原始块分配空文本或按比例分配剩余文本

#### Scenario: 换行符数量多于原始块数量

- **WHEN** 翻译结果包含 M 个换行符
- **AND** 原始块数量为 N（M > N-1）
- **THEN** 将多余的换行符替换为空格
- **AND** 确保拆分后的块数量与原始块数量一致

#### Scenario: 翻译结果不包含换行符

- **WHEN** 翻译结果不包含换行符
- **THEN** 使用原有的按比例拆分逻辑
- **AND** 保持原有行为不变

## MODIFIED Requirements

### Requirement: 修改 split_translated_result 函数

修改 `utils/text_processing.py` 的 `split_translated_result` 函数，在拆分前检测换行符：

修改位置：第431-688行

修改策略：

```python
def split_translated_result(merged_translation, original_blocks):
    """
    拆分翻译结果到原始块
    
    策略：
    1. 检测翻译结果中的换行符数量
    2. 如果换行符数量与原始块数量匹配（换行符数 = 原始块数 - 1），以换行符拆分
    3. 如果不匹配，采用混合策略：
       - 换行符少于原始块：先以换行符拆分，剩余块按比例分配
       - 换行符多于原始块：将多余换行符替换为空格，再拆分
    """
    newline_count = merged_translation.count('\n')
    original_block_count = len(original_blocks)
    
    # 策略1：换行符数量匹配，以换行符拆分
    if newline_count == original_block_count - 1:
        logger.info(f"[换行符拆分] 换行符数量匹配: {newline_count} = 原始块数 {original_block_count} - 1")
        return _split_by_newlines(merged_translation, original_blocks)
    
    # 策略2：换行符少于原始块，混合拆分
    elif newline_count < original_block_count - 1:
        logger.info(f"[换行符拆分] 换行符少于原始块: {newline_count} < {original_block_count - 1}")
        return _split_by_newlines_and_ratio(merged_translation, original_blocks)
    
    # 策略3：换行符多于原始块，替换多余换行符
    elif newline_count > original_block_count - 1:
        logger.info(f"[换行符拆分] 换行符多于原始块: {newline_count} > {original_block_count - 1}")
        return _split_with_excess_newlines(merged_translation, original_blocks)
    
    # 策略4：无换行符，使用原有逻辑
    else:
        logger.info(f"[换行符拆分] 无换行符，使用原有按比例拆分")
        return _split_by_ratio(merged_translation, original_blocks)
```

### Requirement: 添加以换行符拆分的辅助函数

添加 `_split_by_newlines` 函数，以换行符为分隔点拆分：

```python
def _split_by_newlines(merged_translation, original_blocks):
    """以换行符为分隔点拆分翻译结果
    
    Args:
        merged_translation: 合并后的翻译文本
        original_blocks: 原始块列表
        
    Returns:
        list: 拆分后的翻译块列表
    """
    # 以换行符拆分
    lines = merged_translation.split('\n')
    
    # 确保行数与原始块数一致
    if len(lines) != len(original_blocks):
        logger.warning(f"[换行符拆分] 行数不匹配: {len(lines)} vs {len(original_blocks)}")
        # 调整行数
        if len(lines) < len(original_blocks):
            # 补充空行
            lines.extend([''] * (len(original_blocks) - len(lines)))
        else:
            # 合并多余行
            lines[len(original_blocks)-1] = '\n'.join(lines[len(original_blocks)-1:])
            lines = lines[:len(original_blocks)]
    
    # 分配到原始块
    translated_blocks = []
    for i, (line, block) in enumerate(zip(lines, original_blocks)):
        logger.info(f"[换行符拆分] 块 {i+1}: '{line[:50]}...' (长度={len(line)})")
        translated_blocks.append(line)
    
    return translated_blocks
```

### Requirement: 添加混合拆分的辅助函数

添加 `_split_by_newlines_and_ratio` 函数，处理换行符少于原始块的情况：

```python
def _split_by_newlines_and_ratio(merged_translation, original_blocks):
    """混合拆分：先以换行符拆分，剩余块按比例分配
    
    Args:
        merged_translation: 合并后的翻译文本
        original_blocks: 原始块列表
        
    Returns:
        list: 拆分后的翻译块列表
    """
    newline_count = merged_translation.count('\n')
    
    # 先以换行符拆分
    lines = merged_translation.split('\n')
    
    # 前 newline_count + 1 个块使用换行符拆分的结果
    translated_blocks = lines[:newline_count + 1]
    
    # 剩余的原始块按比例分配空文本
    remaining_blocks_count = len(original_blocks) - (newline_count + 1)
    for i in range(remaining_blocks_count):
        translated_blocks.append('')
        logger.info(f"[混合拆分] 块 {newline_count + 2 + i}: 空文本（原始块无对应内容）")
    
    return translated_blocks
```

### Requirement: 添加处理多余换行符的辅助函数

添加 `_split_with_excess_newlines` 函数，处理换行符多于原始块的情况：

```python
def _split_with_excess_newlines(merged_translation, original_blocks):
    """处理多余换行符：替换多余换行符为空格，再拆分
    
    Args:
        merged_translation: 合并后的翻译文本
        original_blocks: 原始块列表
        
    Returns:
        list: 拆分后的翻译块列表
    """
    newline_count = merged_translation.count('\n')
    target_newline_count = len(original_blocks) - 1
    excess_newlines = newline_count - target_newline_count
    
    logger.info(f"[多余换行符处理] 需要替换 {excess_newlines} 个多余换行符")
    
    # 替换多余的换行符为空格
    # 策略：保留前 target_newline_count 个换行符，替换后面的
    lines = merged_translation.split('\n')
    
    # 前 target_newline_count + 1 行保持不变
    preserved_lines = lines[:target_newline_count + 1]
    
    # 多余的行合并到最后一行（用空格连接）
    excess_lines = lines[target_newline_count + 1:]
    if excess_lines:
        preserved_lines[-1] = preserved_lines[-1] + ' ' + ' '.join(excess_lines)
        logger.info(f"[多余换行符处理] 合并多余行到最后一行")
    
    return preserved_lines
```

## REMOVED Requirements

（无移除的需求）

## 验证方法

### 测试场景1：换行符数量匹配

原文：
```
块1: "When zero-shot doesn't work, you can provide demonstrations or examples in the prompt,"
块2: "which leads to "one-shot" and "few-shot" prompting."
```

翻译结果：
```
"当零样本方法不奏效时，你可以在提示词中提供示例或演示，
这会引出"单样本"和"少样本"提示方法。"
```

预期拆分结果：
```
块1: "当零样本方法不奏效时，你可以在提示词中提供示例或演示，"
块2: "这会引出"单样本"和"少样本"提示方法。"
```

### 测试场景2：换行符少于原始块

原文：
```
块1: "First line"
块2: "Second line"
块3: "Third line"
```

翻译结果：
```
"第一行
第二行"
```

预期拆分结果：
```
块1: "第一行"
块2: "第二行"
块3: ""
```

### 测试场景3：换行符多于原始块

原文：
```
块1: "First line"
块2: "Second line"
```

翻译结果：
```
"第一行
第二行
第三行"
```

预期拆分结果：
```
块1: "第一行"
块2: "第二行 第三行"
```

### 测试场景4：无换行符

原文：
```
块1: "First line"
块2: "Second line"
```

翻译结果：
```
"第一行第二行"
```

预期行为：使用原有按比例拆分逻辑