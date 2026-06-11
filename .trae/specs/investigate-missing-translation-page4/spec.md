# 调查翻译丢失第四页以下内容 Spec

## Why

用户报告最后一次翻译丢失了第四页以下的内容，具体包括 "Overflow surface load, • 5,0 m/h at Qdim • 7,8 m/h at Qmaksdim" 等技术规格文本。需要排查内容是在 OCR 提取阶段丢失，还是在提取后翻译阶段丢失。

## What Changes

- 在 OCR 提取阶段增加诊断日志，记录每个页面 PaddleOCR 返回的所有版面标签及对应内容
- 在翻译流水线各关键节点增加内容完整性校验
- 修复 `TEXT_LABELS` 集合可能遗漏的版面标签（如 `list`、`list_item` 等）
- 修复 `split_translated_result` 中提前退出导致后续块内容丢失的问题

## Impact

- Affected specs: OCR提取完整性、翻译内容完整性
- Affected code:
  - `modules/ocr/paddle_extractor.py` — `TEXT_LABELS`、`NON_BODY_LABELS`、`_process_page_layout`
  - `utils/text_processing.py` — `split_translated_result`
  - `services/translation_service.py` — `extract_pdf_content`

## 根因分析

经过对完整翻译流水线的代码审查，识别出以下 **5 个可能导致内容丢失的环节**：

### 环节1: OCR 版面标签遗漏（最高嫌疑）

[paddle_extractor.py:77-83](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L77-L83) 定义的 `TEXT_LABELS` 集合：

```python
TEXT_LABELS = {
    'text', 'title', 'content', 'document_title', 'section_title',
    'abstract', 'references', 'reference', 'footnote',
    'header', 'footer', 'page_number',
    'sidebar_text', 'text_continue',
    'table_caption', 'table_footnote',
}
```

**问题**：PaddleOCR PP-StructureV3 可能返回 `list`、`list_item`、`item` 等标签来标识列表内容。这些标签不在 `TEXT_LABELS` 中，导致列表内容（如 "Overflow surface load, • 5,0 m/h at Qdim • 7,8 m/h at Qmaksdim"）被完全跳过——既不作为文本块提取，也不作为图像/表格/公式处理。

在 [paddle_extractor.py:397](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L397) 中，只有 `label in self.TEXT_LABELS` 的块才会被提取为文本块：

```python
if label in self.TEXT_LABELS:
    # 提取文本...
elif label == 'table':
    has_table = True
elif label in ('formula', 'formula_number'):
    has_formula = True
elif label in self.IMAGE_LABELS:
    # 提取图像...
# 其他标签完全被忽略！
```

### 环节2: `is_body_text` 过滤

[paddle_extractor.py:86](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L86) 定义的 `NON_BODY_LABELS`：

```python
NON_BODY_LABELS = {'header', 'footer', 'page_number', 'footnote'}
```

如果 PaddleOCR 将列表内容误分类为 `header`、`footer`、`page_number` 或 `footnote`，则该内容会被标记为 `is_body_text = False`（[paddle_extractor.py:466-467](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L466-L467)），随后在 [translation_service.py:305](file:///Users/chunju/work/pdfTrans/services/translation_service.py#L305) 被过滤掉：

```python
if text_block.is_body_text:
    text_blocks.append(text_block)
```

### 环节3: `split_translated_result` 提前退出

[text_processing.py:501-503](file:///Users/chunju/work/pdfTrans/utils/text_processing.py#L501-L503) 中，当翻译文本耗尽时提前退出循环：

```python
if start_pos >= translation_len:
    logger.info(f"已到达文本末尾，跳出循环，处理了 {i+1} 个块")
    break
```

这会导致后续所有块获得空字符串内容。当翻译结果比原文短（例如中译英时中文更紧凑），或者翻译被截断时，此问题尤为严重。

### 环节4: 翻译截断

翻译 API 可能截断长文本的翻译结果。虽然 [translation_service.py:355-363](file:///Users/chunju/work/pdfTrans/services/translation_service.py#L355-L363) 检查了 `truncated` 标志并记录警告，但截断的翻译结果仍然被使用，导致后续块内容丢失。

### 环节5: 子进程序列化/反序列化

OCR 在子进程中运行，结果通过 `to_dict()` / `from_dict()` 序列化传递。[extraction.py:299-310](file:///Users/chunju/work/pdfTrans/models/extraction.py#L299-L310) 的序列化逻辑看起来完整，但如果 `text_blocks` 中有异常数据（如 `None` 值），可能导致反序列化失败，进而丢失整个页面的数据。

## ADDED Requirements

### Requirement: OCR 版面标签完整性

系统 SHALL 在 `_process_page_layout` 中记录所有 PaddleOCR 返回的版面标签，包括不在 `TEXT_LABELS` 中的标签。对于未知标签，系统 SHALL 将其视为正文文本进行提取，而非静默跳过。

#### Scenario: PaddleOCR 返回未知版面标签
- **WHEN** PaddleOCR 返回一个不在 `TEXT_LABELS`、`IMAGE_LABELS`、`table`、`formula` 中的版面标签
- **THEN** 系统应记录警告日志，包含标签名称和对应文本内容
- **AND** 系统应将该内容作为正文文本块提取（`is_body_text = True`）
- **AND** 翻译结果中应包含该内容

#### Scenario: PaddleOCR 返回列表类标签
- **WHEN** PaddleOCR 返回 `list`、`list_item`、`item` 等列表相关标签
- **THEN** 系统应将这些标签视为正文文本标签
- **AND** 列表内容应被完整提取并翻译

### Requirement: 翻译拆分结果完整性校验

系统 SHALL 在 `split_translated_result` 完成拆分后校验所有块是否有内容。如果存在空块，系统 SHALL 记录警告并尝试从相邻块分配内容。

#### Scenario: 翻译结果比原文短导致部分块为空
- **WHEN** 翻译结果文本长度不足以分配给所有原始块
- **THEN** 系统应记录警告，包含原始块数量、翻译文本长度、空块数量
- **AND** 空块应使用原文作为回退内容

#### Scenario: 翻译被截断
- **WHEN** 翻译 API 返回截断的结果
- **THEN** 系统应记录警告
- **AND** 未被翻译覆盖的原始块应保留原文

### Requirement: 提取阶段内容完整性日志

系统 SHALL 在 OCR 提取完成后记录每页的内容完整性摘要，包括提取的文本块数量、被跳过的标签及数量、`is_body_text = False` 的块数量。

#### Scenario: OCR 提取完成
- **WHEN** OCR 提取完成一个页面的内容
- **THEN** 系统应记录该页面的标签统计、文本块数量、被跳过的内容摘要
- **AND** 如果有内容被跳过，应记录警告级别的日志

## MODIFIED Requirements

无

## REMOVED Requirements

无
