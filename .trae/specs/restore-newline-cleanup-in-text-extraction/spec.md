# 恢复文本提取时清理换行符功能 Spec

## Why

从日志第47-68行可以看到，标题 "2.3 EXECUTION OF GROUND INVESTIGATION" 翻译后显示为 "2.3..."，文本被过度截断。根因是翻译文本包含换行符 `"2.3\n地质勘察的实施"`，导致文本被分成两行，但文本框高度不足以容纳多行。

**正确的解决方案**：在文本提取阶段清理换行符，确保标题文本是单行，而非在渲染阶段扩展文本框高度。

## 根因分析

### 换行符来源

从日志第48-49行：
```
溢出文本: '2.3
地质勘察的实施...' (完整长度=11)
```

文本包含换行符，可能来源：
1. **原文本身就是分行的**：标题号 "2.3" 和标题内容 "EXECUTION OF GROUND INVESTIGATION" 在原文PDF中就是分开的（不同行或不同文本块）
2. **OCR提取保留了换行符**：OCR识别时保留了原文的换行符结构
3. **文本块合并时引入换行符**：多个文本块合并时使用了换行符作为分隔符

### 问题链

1. **文本提取保留了换行符** → 标题文本包含 `\n`
2. **翻译保留了换行符** → 翻译API返回的文本也包含 `\n`
3. **文本框高度不足** → 文本框高度13.3pt只能容纳1行，但文本需要2行
4. **触发截断逻辑** → 最终截断到40%，只剩 "2.3..."

### 正确的解决方案

**在文本提取阶段清理换行符**：
- 对于标题文本（`paragraph_title`、`title`等标签），清理换行符，确保是单行
- 对于正文文本，保留换行符（因为正文可能需要多行）
- 清理策略：将 `\n` 替换为空格或直接删除

## What Changes

- **恢复文本提取时的换行符清理功能**：在OCR提取和文本块创建时，对标题类文本清理换行符
- **区分标题和正文**：标题文本清理换行符，正文文本保留换行符
- **清理策略**：将 `\n` 替换为空格（保持语义完整性）

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`、`modules/pdf_extractor.py`
- 行为变更：标题类文本在提取时会清理换行符，确保是单行
- 影响范围：所有文本提取，特别是标题和短文本块

## ADDED Requirements

### Requirement: 文本提取时清理标题文本的换行符

系统 SHALL 在提取文本时，对标题类文本（`paragraph_title`、`title`、`section_title`等标签）清理换行符，确保标题是单行。

#### Scenario: 标题文本包含换行符

- **WHEN** OCR识别到标题文本包含换行符（`\n`）
- **THEN** 系统将换行符替换为空格：`text.replace('\n', ' ')`
- **AND** 清理多余空格：`text.strip()` 和 `' '.join(text.split())`
- **AND** 确保标题是单行文本

#### Scenario: 正文文本包含换行符

- **WHEN** OCR识别到正文文本包含换行符
- **THEN** 保留换行符（正文可能需要多行）
- **AND** 不清理换行符

#### Scenario: 清理换行符日志

- **WHEN** 清理标题文本的换行符
- **THEN** 记录日志：原始文本、清理后文本、换行符数量

## MODIFIED Requirements

### Requirement: OCR提取时清理标题文本换行符

修改 `modules/ocr/paddle_extractor.py` 的文本提取逻辑，在创建TextBlock时对标题类文本清理换行符：

修改前：
```python
# 直接使用OCR识别的文本
text = textline_texts[i].strip()
```

修改后：
```python
# 清理标题文本的换行符
text = textline_texts[i].strip()
if label in ['paragraph_title', 'title', 'section_title']:
    # 清理换行符，确保标题是单行
    original_text = text
    text = text.replace('\n', ' ').strip()
    text = ' '.join(text.split())  # 清理多余空格
    if '\n' in original_text:
        logger.info(f"[换行符清理] 标题文本清理换行符: '{original_text[:30]}' -> '{text[:30]}'")
```

### Requirement: 非OCR提取时清理标题文本换行符

修改 `modules/pdf_extractor.py` 的文本提取逻辑，在创建TextBlock时对标题类文本清理换行符：

修改前：
```python
# 直接使用PyMuPDF提取的文本
text = block['text'].strip()
```

修改后：
```python
# 清理标题文本的换行符
text = block['text'].strip()
if is_title_text(block):  # 根据字体大小、位置等判断是否是标题
    original_text = text
    text = text.replace('\n', ' ').strip()
    text = ' '.join(text.split())  # 清理多余空格
    if '\n' in original_text:
        logger.info(f"[换行符清理] 标题文本清理换行符: '{original_text[:30]}' -> '{text[:30]}'")
```

## REMOVED Requirements

（无移除的需求）