# 修复公式 LaTeX 在 DOCX/MD 输出中重复或未正确包裹 Spec

## Why

当前公式处理存在两个问题：

**问题 1 — DOCX 中公式 LaTeX 重复输出**：`_add_merged_text` 对包含公式块的 `MergedBlock` 先插入 OMML（正确渲染公式），然后又通过 `translated_item.block_text` 将整个文本（含 LaTeX 代码）作为普通文本再次写入段落。导致同一公式在 DOC 中同时以渲染公式和 LaTeX 源码文本形式重复出现。示例：`SOTR{ = }\frac{f_{\mathrm{d}} \cdot \beta_{S t} \cdots}` 在公式后面重复出现。

**问题 2 — MD 中公式未用 `$`/`$$` 包裹**：`_process_page_elements` 和 `_insert_element_in_merged_block` 中通过 `getattr(block, 'is_formula', False)` 判断是否为公式，但公式 TextBlock 被包装为 `MergedBlock` 时，`MergedBlock` 自身没有 `is_formula` 属性。导致公式 LaTeX 未被 `$...$`/`$$...$$` 包裹就直接送入 LLM 布局格式化，LLM 可能剥离 `$` 标记、转义 `$` 符号或将公式当作普通文本重新排版，最终公式在 MD 中显示不正确。

## What Changes

1. **MergedBlock 增加 `is_formula` 属性**：在创建 MergedBlock 时，根据 `original_blocks` 中是否有 `is_formula=True` 的块来自动设置 `is_formula`
2. **DOCX 端修复**：在 `_add_merged_text` 中，写入 `block_text` 作为普通文本前，移除其中与公式 `block_text` 匹配的部分
3. **MD 端修复**：利用 MergedBlock 的 `is_formula` 属性，使 `_process_page_elements` 和 `_insert_element_in_merged_block` 中的公式包裹逻辑正确触发

## Impact

- Affected code:
  - `models/merged_block.py` — MergedBlock 增加 `is_formula` 属性
  - `modules/docx_generator.py` — `_add_merged_text` 移除公式文本
  - `modules/markdown_generator.py` — 公式包裹逻辑利用新属性
- 行为变更：
  - DOCX 输出中公式 LaTeX 不再以普通文本重复出现
  - MD 输出中公式被正确 `$`/`$$` 包裹，LLM 不再破坏公式内容

## ADDED Requirements

### Requirement: MergedBlock 自动检测公式属性

MergedBlock 在初始化时 SHALL 通过检查 `original_blocks` 中是否有 `is_formula=True` 的块来自动设置自身的 `is_formula` 属性。

#### Scenario: 包含公式块

- **WHEN** `original_blocks` 中存在 `is_formula=True` 的块
- **THEN** `self.is_formula = True`

#### Scenario: 不含公式块

- **WHEN** `original_blocks` 中没有任何 `is_formula=True` 的块
- **THEN** `self.is_formula = False`（默认）

### Requirement: DOCX 公式文本不重复输出

当 `_add_merged_text` 处理包含公式块的 `translated_item` 时，SHALL 从 `block_text` 中移除公式块对应的 LaTeX 文本后再写入普通文本段落。

#### Scenario: MergedBlock 包含公式块

- **WHEN** `translated_item.original_blocks` 中存在 `is_formula=True` 的块
- **AND** 这些块的 `block_text` 出现在 `translated_item.block_text` 中
- **THEN** 从 `text_to_write` 中移除公式文本，移除后清理多余空白
- **THEN** 公式仍通过 `_insert_formula_omml` 插入 OMML 渲染

#### Scenario: MergedBlock 不包含公式块

- **WHEN** `translated_item.original_blocks` 中无公式块
- **THEN** 行为不变，`block_text` 正常作为普通文本输出

#### Scenario: 纯公式块（original_blocks 只有公式）

- **WHEN** `translated_item.original_blocks` 中所有块均为公式
- **THEN** 移除全部公式文本后 `text_to_write` 为空，不写入普通文本 run

### Requirement: MD 公式被正确包裹

`_process_page_elements` 和 `_insert_element_in_merged_block` 中，通过检查 `block.is_formula`（MergedBlock 新属性）来判断是否为公式，对公式 LaTeX 文本用 `$`（行内）或 `$$`（独立行）包裹。

#### Scenario: 行内公式

- **WHEN** `block.is_formula = True` 且公式块宽度 < 页面宽度 × 60%
- **THEN** 输出 `$latex_text$`

#### Scenario: 独立行公式

- **WHEN** `block.is_formula = True` 且公式块宽度 ≥ 页面宽度 × 60%
- **THEN** 输出 `$$latex_text$$`

## MODIFIED Requirements

### Requirement: `_add_merged_text` 增加公式文本移除逻辑

```python
def _add_merged_text(self, doc, translated_item):
    paragraph = doc.add_paragraph()

    if hasattr(translated_item, 'original_blocks') and translated_item.original_blocks:
        # 先处理 formula 块（需要按块插入 OMML）
        for text_block in translated_item.original_blocks:
            if getattr(text_block, 'is_formula', False) and text_block.block_text:
                self._insert_formula_omml(paragraph, text_block.block_text)

        # 有翻译文本时只写入一次，避免重复
        if hasattr(translated_item, 'block_text') and translated_item.block_text:
            text_to_write = translated_item.block_text
            # 移除公式文本，避免在普通文本中重复输出公式 LaTeX
            for text_block in translated_item.original_blocks:
                if getattr(text_block, 'is_formula', False) and text_block.block_text:
                    if text_block.block_text in text_to_write:
                        text_to_write = text_to_write.replace(text_block.block_text, '')
            # 清理多余空白
            import re
            text_to_write = re.sub(r'  +', ' ', text_to_write).strip()
        elif translated_item.original_blocks:
            text_to_write = translated_item.original_blocks[0].block_text
        else:
            text_to_write = ''

        if text_to_write.strip():
            cleaned_text = self._clean_xml_compatible_text(text_to_write)
            run = paragraph.add_run(cleaned_text)
            # 样式设置不变...
```

## REMOVED Requirements

无
