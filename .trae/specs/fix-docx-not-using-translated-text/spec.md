# 修复 DOCX 输出使用原始英文文本而非翻译文本 Spec

## Why

最后一次生成 `output_format=all` 时，PDF 输出正确显示了中文翻译，但 DOCX 输出了原始英文文本。

**根因分析**：

在 `docx_generator.py` 的 `_add_merged_text` 方法（第686-711行）中，写入 DOCX 时使用了 `original_blocks` 中 TextBlock 的 `block_text`（原始英文），而非 MergedBlock 的 `block_text`（翻译中文）。

这个变量名 `merged_item` 容易让人误解——您当前不使用语义合并（`semantic_merge=False`），但 `merged_translations` 列表中的每个元素仍然是 `MergedBlock` 对象。MergedBlock 在整个代码中统一承担"翻译结果容器"的角色，无论是否开启了语义合并。

**数据流追踪（非语义合并路径）**：

```
translation_service.py::translate_original_block()  ← 每个原始块被提交翻译
    │  translator.translate(text_block.block_text, ...)  ← 调用翻译 API
    │  translated_text = translation_result.content       ← "智能体与智能体架构简介"
    │
    │  # 创建 MergedBlock，这里就是"翻译结果容器"
    │  translated_merged_block = MergedBlock(
    │      block_text=translated_text,          ← block_text = 翻译后的中文 ✓
    │      original_blocks=[block_info],        ← 原始英文 TextBlock（保留样式信息）
    │      max_width=width,
    │      max_height=height
    │  )
    │
    ▼
process_original_blocks()  ← 收集所有翻译结果
    │  merged_translations = []
    │  merged_translations.append(translated_merged_block)  ← 加入列表
    │
    ▼
translated_content['merged_translations'] = merged_translations
    │
    ▼
docx_generator.py::_add_merged_text()
    │  # merged_item = MergedBlock
    │  #   merged_item.block_text = "智能体与智能体架构简介"   ← ✓ 翻译文本
    │  #   merged_item.original_blocks[0].block_text = "Introduction to..." ← 原始英文
    │
    ├── line 687: for text_block in merged_item.original_blocks:
    ├── line 691: cleaned_text = self._clean_xml_compatible_text(text_block.block_text)
    │                                    ↑ BUG: 用了原始英文文本！
    └── line 694: run = paragraph.add_run(cleaned_text)
                  → DOCX 输出的是原始英文！✗
```

**对比 PDF 生成（为什么 PDF 正确）**：

PDF 生成器不使用 `merged_translations`，而是使用 `translated_content['blocks']`：
- `pdf_generator.py` 使用 `PdfPage.text_blocks` → `translated_text_block.block_text`
- `translated_text_block` 在 `translate_original_block` 第625-626行被正确设置：
  ```python
  translated_text_block = text_block.copy()
  translated_text_block.block_text = translated_text  # ← 翻译文本
  ```
- 所以 PDF 始终显示中文 ✓

## What Changes

### 变更1：`_add_merged_text` 使用翻译文本

修改 `docx_generator.py` 第691行，将 `text_block.block_text`（原始文本）改为 `merged_item.block_text`（翻译文本）。

修改前：
```python
cleaned_text = self._clean_xml_compatible_text(text_block.block_text)
```

修改后：
```python
use_text = merged_item.block_text if hasattr(merged_item, 'block_text') and merged_item.block_text else text_block.block_text
cleaned_text = self._clean_xml_compatible_text(use_text)
```

公式处理（第688-689行）保持不变，因为公式文本不被翻译，本身就是原始内容。

### 变更2：重命名容易误解的变量名

`_add_merged_text` 方法的参数 `merged_item` 暗示"只有语义合并时才可用"，实际上无论是否开启语义合并，该对象始终包含翻译结果。将其重命名为 `translated_item`，消除误导。

修改前：
```python
def _add_merged_text(self, doc, merged_item, preserve_formatting=True):
```

修改后：
```python
def _add_merged_text(self, doc, translated_item, preserve_formatting=True):
```

同时更新方法体内所有 `merged_item.xxx` → `translated_item.xxx` 的引用。由于这是方法参数和局部变量，重命名局限于此方法内，零风险。

同样更新 `_add_paragraph_elements` 方法中调用 `_add_merged_text` 处的变量名：
```python
# 修改前
self._add_merged_text(doc, block, preserve_formatting)

# 修改后  
self._add_merged_text(doc, translated_block, preserve_formatting)
```

## Impact

- Affected code: `modules/docx_generator.py`

## ADDED Requirements

（无新增需求）

## MODIFIED Requirements

### Requirement: `_add_merged_text` 使用翻译文本而非原始文本

修改 `docx_generator.py` 的 `_add_merged_text` 方法，在写入非公式文本时使用 `merged_item.block_text`（翻译文本）而非 `text_block.block_text`（原始文本）。

#### Scenario: 非公式文本块

- **WHEN** `_add_merged_text` 处理包含 `original_blocks` 的 `merged_item`
- **AND** 当前 `text_block` 不是公式块
- **THEN** 使用 `merged_item.block_text` 作为写入 DOCX 的文本内容
- **AND** 文本样式（字体、字号、颜色等）仍然从当前 `text_block` 获取

#### Scenario: 公式文本块

- **WHEN** `_add_merged_text` 处理公式块（`text_block.is_formula = True`）
- **THEN** 保持现有行为，使用 `text_block.block_text` 插入 OMML 公式

## REMOVED Requirements

（无移除的需求）

## 验证方式

1. 对包含文本的 PDF 运行 `output_format=all`，生成的 DOCX 文件内容应为中文而非英文
2. 对包含公式的 PDF 验证公式在 DOCX 中正常显示
3. 对比 DOCX 和 PDF 的翻译一致性
