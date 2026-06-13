# 统一在提取阶段清理换行符 Spec

## Why

当前换行符处理分散在整个管道的多个阶段，逻辑混乱且不一致：

| 阶段 | 文件 | 行为 | 问题 |
|------|------|------|------|
| OCR提取 | `paddle_extractor.py:615-624` | 仅对标题类文本删除`\n` | 规则不一致 |
| PDF提取 | `pdf_extractor.py:420` | 完全保留原始换行符 | 无任何处理 |
| 合并前 | `text_processing.py:1035` | `strip()`去尾部空白 | 只对发往LLM的副本处理 |
| 翻译前 | `translator.py:120-131` | `_preprocess_text`按`\n`分割清理 | 逻辑重复 |
| 翻译提示词 | `translator.py:154-158` | 要求LLM保持换行符一致 | 过于严格，LLM难以遵守 |
| 翻译后 | `translator.py:66-78` | `_postprocess_text`清理行内空格 | 同样重复 |

根因：**提取阶段未统一清理换行符，导致后续阶段被迫做各种补偿处理**。

**统一策略**：在提取阶段（文本块和表格文本创建后）统一删除换行符（`\n`），然后删除所有后续阶段的换行符补偿处理代码。

## What Changes

### 1. 提取后统一删除换行符

在文本块和表格单元格文本创建后，对所有文本删除换行符（`text.replace('\n', '')`）。

应用位置：
- **OCR提取** `paddle_extractor.py`：在 `_build_text_from_textlines` 返回前统一删除（移除仅对标题删除的特殊逻辑）
- **PDF提取** `pdf_extractor.py`：在 `_extract_text_blocks` 创建 TextBlock 后统一删除
- **表格文本（OCR）**：在解析 HTML 表格单元格文本时删除
- **表格文本（PDF）**：在 `extract_tables_by_pymupdf` 中删除单元格文本
- **补充文本块**：OCR 补充捕获阶段创建的 TextBlock 也需删除

### 2. 删除翻译阶段的换行符处理

- `translator.py` 删除 `_preprocess_text` 方法和 `_postprocess_text` 方法中的 `\n` 相关逻辑
- `translator.py` 删除系统提示词第7条"保持换行符一致性"规则（第154-158行）

### 3. 删除合并阶段的换行符相关注释

- `text_processing.py` 第1033-1035行，移除注释中关于换行符的说明

### 4. 删除或清理CHANGELOG中的相关条目

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`, `modules/pdf_extractor.py`, `modules/translator.py`, `utils/text_processing.py`
- 行为变更：所有文本块（标题和正文）的换行符在提取阶段统一删除
- 翻译阶段不再关心换行符，简化翻译逻辑
- 拆分阶段不再需要处理换行符
- **BREAKING**：原文中的换行符将被全部删除，不再保留

## ADDED Requirements

### Requirement: 提取后统一删除换行符

提取完成后，对所有文本块（TextBlock）和表格单元格文本执行换行符删除。

#### Scenario: 文本块创建后删除

- **WHEN** 提取阶段创建 TextBlock 对象
- **THEN** 对 `block_text` 删除换行符：`text.replace('\n', '')`

#### Scenario: 表格单元格文本删除

- **WHEN** 提取阶段创建表格单元格（PdfCell）对象
- **THEN** 对单元格 `text` 执行同样的 `replace('\n', '')` 操作

## MODIFIED Requirements

### Requirement: 修改 OCR 提取阶段

**文件**: `modules/ocr/paddle_extractor.py`

修改 `_build_text_from_textlines`，将换行符处理从不分标题/正文的通用处理：

修改前：
```python
result = '\n'.join(lines)

# 对标题类文本清理换行符
if is_title and result and '\n' in result:
    original_text = result
    result = result.replace('\n', '')
    ...
```

修改后：
```python
result = '\n'.join(lines)

# 统一删除换行符（标题和正文均处理）
if result and '\n' in result:
    original_text = result
    result = result.replace('\n', '')
    ...
```

### Requirement: 修改 PDF 提取阶段

**文件**: `modules/pdf_extractor.py`

在 `_extract_text_blocks` 中创建 TextBlock 后，添加换行符删除逻辑：

```python
# 创建TextBlock对象
text_block = TextBlock(...)
# 删除换行符
if '\n' in text:
    text_block.block_text = text.replace('\n', '')
```

### Requirement: 修改表格提取

**文件**: `modules/pdf_extractor.py` 和 `modules/ocr/paddle_extractor.py`

对表格单元格文本同样执行换行符删除。

### Requirement: 删除翻译阶段的换行符处理

**文件**: `modules/translator.py`

- 删除或简化 `_preprocess_text` 方法（移除 `text.split('\n')` 相关逻辑）
- 删除或简化 `_postprocess_text` 方法（移除 `processed_text.split('\n')` 相关逻辑）
- 删除系统提示词中第7条"保持换行符一致性"规则（第154-158行）

## REMOVED Requirements

### Requirement: 翻译阶段保持换行符一致性

**Reason**: 提取阶段已统一删除换行符，翻译阶段不再需要关心换行符结构
**Migration**: 删除系统提示词第7条换行符保持规则，删除 `_preprocess_text`/`_postprocess_text` 中的 `\n` 逻辑

### Requirement: 拆分阶段处理标题换行符

**Reason**: 所有换行符在提取阶段已被删除，拆分阶段不需要再处理
**Migration**: 无需在 `split_translated_result` 中添加 `_is_title_block` 等换行符清理逻辑
