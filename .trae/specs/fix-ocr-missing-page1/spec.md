# OCR 翻译结果缺失第一页 Spec

## Why
OCR 模式下，当 PPStructureV3 将某页（如第一页）完全分类为图像时，该页没有任何文本块被提取，导致翻译服务和 PDF 生成器跳过该页，最终输出 PDF 缺失该页。

## What Changes
- 修复翻译服务：确保所有提取到的页面（包括无文本块的页面）都保留在翻译结果中
- 修复 PDF 生成器：确保输出 PDF 包含原始 PDF 的所有页面，即使某些页面没有翻译内容也保留原始页面
- 在 `_process_page_layout` 中添加调试日志，记录每页的版面分析结果摘要

## Impact
- Affected specs: font-debug-log-missing（日志修复已生效，确认了此问题）
- Affected code: `services/translation_service.py`, `modules/pdf_generator.py`, `modules/ocr/paddle_extractor.py`

## 深度分析：根因

### 日志证据

最后一次运行（13:19-13:28）的关键日志：

```
13:19:09 - 开始OCR提取PDF: test_data_ocr.pdf, 共3页
13:19:23 - PPStructureV3 构造修改了 root logger level (INFO -> WARNING)，正在恢复  ← 修复生效！
13:19:23 - 步骤1管线创建: 内存使用 771 MB
           ← page=1 处理耗时约6分钟，但无任何 FONT_DEBUG 日志
13:25:02 - [FONT_DEBUG] page=2, label=text, ...  ← page=2 有文本块
13:27:46 - [FONT_DEBUG] page=3, label=text, ...  ← page=3 有文本块
13:27:48 - OCR提取完成: 共3页, 0个表格, 5个图像
13:27:49 - 提取到的blocks信息: 总页数=3
13:27:49 - 共提取到 11 个完整文本块
13:28:50 - 传递给生成器的blocks信息: 总页数=2, 总blocks数=9  ← 只有2页！
13:28:50 - 第 2 页有 6 个完整文本块
13:28:50 - 第 3 页有 3 个完整文本块
13:28:50 - PDF生成完成，总页数: 2  ← 输出只有2页！
```

### 问题链

**问题 1：PPStructureV3 将第 1 页完全分类为图像**

- 第 1 页的图像区域 bbox 为 `(10.19, 83.95, 585.08, 755.54)`，几乎覆盖整页
- PPStructureV3 将第 1 页内容标记为 `image`/`figure` 标签，而非 `text` 标签
- 因此 `_process_page_layout` 没有为第 1 页生成任何 TextBlock
- `paddle_extractor.py` 的 `extract_from_pdf` 仍会为第 1 页创建 `PdfPage(page_num=1, text_blocks=[])`

**问题 2：翻译服务丢弃无文本块的页面**

- `translation_service.py` 第 1519 行：
  ```python
  translated_content['blocks'] = [page_translated_blocks_dict[page_num] for page_num in sorted(page_translated_blocks_dict.keys())]
  ```
- `page_translated_blocks_dict` 只包含有文本块的页面
- 第 1 页没有文本块，从未被添加到 `page_translated_blocks_dict`
- 因此 `translated_content['blocks']` 只包含第 2、3 页

**问题 3：PDF 生成器只处理有翻译内容的页面**

- `pdf_generator.py` 第 88-100 行：
  ```python
  pages_with_content = set()
  for blocks_content in translated_content.get('blocks', []):
      pages_with_content.add(blocks_content.page_num)
  for table_content in translated_content.get('tables', []):
      pages_with_content.add(table_content.page_num)
  pages_to_process = sorted(pages_with_content)
  ```
- 只有出现在 `blocks` 或 `tables` 中的页面才会被处理
- 第 1 页既没有文本块也没有表格，完全被跳过
- 输出 PDF 只有 2 页

### 根因总结

PPStructureV3 将某些页面（如封面、图片页）完全分类为图像是正常行为。但系统没有正确处理"有页面但无文本块"的情况，导致这些页面在翻译流程中被丢弃。

## ADDED Requirements

### Requirement: 翻译服务保留所有页面
翻译服务 SHALL 确保所有从 OCR 提取结果中获得的页面（包括 `text_blocks` 为空的页面）都保留在 `translated_content['blocks']` 中。

#### Scenario: 页面无文本块时仍保留在翻译结果中
- **WHEN** OCR 提取结果包含某页但该页 `text_blocks` 为空
- **THEN** 该页 SHALL 仍以 `PdfPage(page_num=N, text_blocks=[])` 的形式出现在 `translated_content['blocks']` 中

### Requirement: PDF 生成器包含所有原始页面
PDF 生成器 SHALL 确保输出 PDF 包含原始 PDF 的所有页面。对于没有翻译内容的页面，SHALL 直接复制原始页面内容。

#### Scenario: 页面无翻译内容时保留原始页面
- **WHEN** 原始 PDF 有 N 页，但只有 M 页有翻译内容（M < N）
- **THEN** 输出 PDF SHALL 仍包含 N 页
- **AND** 无翻译内容的页面 SHALL 直接复制原始页面

### Requirement: 版面分析调试日志
`_process_page_layout` 方法 SHALL 为每页输出版面分析摘要日志，包括检测到的各类标签数量，便于诊断页面被分类为图像的问题。

#### Scenario: 页面被完全分类为图像
- **WHEN** PPStructureV3 将某页的所有内容分类为 image/figure 标签
- **THEN** 日志 SHALL 记录该页的标签分布，如 "page=1: text=0, image=1, table=0, formula=0"

## MODIFIED Requirements

### Requirement: PDF 生成器页面处理逻辑
PDF 生成器 SHALL 从原始 PDF 的所有页面生成输出，而非仅从有翻译内容的页面生成。对于有翻译内容的页面，覆盖翻译文本；对于无翻译内容的页面，直接复制原始页面。

## REMOVED Requirements
无
