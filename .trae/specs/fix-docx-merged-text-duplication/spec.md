# 修复语义合并块在 DOCX 中重复输出 Spec

## Why

语义合并路径下，多个原始块（例如 4 个）被合并为一个 `MergedBlock`，`_add_merged_text` 遍历 `original_blocks` 时每次都写入完整的 `block_text`，导致同一段翻译文本在 DOCX 中重复输出 N 次。

## What Changes

修改 `_add_merged_text`：当有翻译文本（`translated_item.block_text`）时，**只写入一次**完整文本，不再为每个 `original_block` 重复写入。仅对 formula 块保留遍历逻辑。

## Impact

- Affected code: `modules/docx_generator.py`（`_add_merged_text` 方法）

## ADDED Requirements

### Requirement: 语义合并文本只写入一次

当 `translated_item` 拥有 `block_text`（翻译文本）时，SHALL 只写入一次，避免重复。

#### Scenario: original_blocks 有多个且翻译文本存在

- **WHEN** `translated_item.original_blocks` 有多个块
- **AND** `translated_item.block_text` 非空
- **THEN** 写入 `block_text` 一次，不再为每个 original_block 重复写入

#### Scenario: 包含 formula 块

- **WHEN** `original_blocks` 中存在 `is_formula=True` 的块
- **THEN** formula 块仍然调用 `_insert_formula_omml` 处理

## MODIFIED Requirements

### Requirement: `_add_merged_text` 改写

将遍历 `original_blocks` 每次写完整文本的逻辑，改为：**当有翻译文本时只写一次**，只遍历 `original_blocks` 处理特殊 case（公式等）。

```python
def _add_merged_text(self, doc, translated_item):
    paragraph = doc.add_paragraph()

    if hasattr(translated_item, 'original_blocks') and translated_item.original_blocks:
        # 先处理 formula 块（需要按块插入 OMML）
        has_formula = any(getattr(b, 'is_formula', False) and b.block_text for b in translated_item.original_blocks)
        if has_formula:
            for text_block in translated_item.original_blocks:
                if getattr(text_block, 'is_formula', False) and text_block.block_text:
                    self._insert_formula_omml(paragraph, text_block.block_text)

        # 有翻译文本时只写入一次，避免重复
        if hasattr(translated_item, 'block_text') and translated_item.block_text:
            text_to_write = translated_item.block_text
        elif translated_item.original_blocks:
            text_to_write = translated_item.original_blocks[0].block_text
        else:
            text_to_write = ''

        if text_to_write.strip():
            cleaned_text = self._clean_xml_compatible_text(text_to_write)
            run = paragraph.add_run(cleaned_text)
            # 样式设置...
    else:
        # 无 original_blocks，直接写 block_text
        cleaned_text = self._clean_xml_compatible_text(translated_item.block_text)
        run = paragraph.add_run(cleaned_text)
        # ...
```

## REMOVED Requirements

无