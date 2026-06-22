# 修复 PaddleOCR 表格单元格错误合并 Spec

## Why
PaddleOCR PPStructureV3 对第64页表格的 HTML 输出存在错误：将第5行第0列（"OpenWebText2"）和第5行第1列（"Outbound Reddit links"）的内容输出到同一个 `<td>` 标签中，导致 `_TableHtmlParser` 将两者无分隔地拼接为 "OpenWebText2Outbound Reddit链接"。翻译后 LLM 将其翻译为 "OpenWebText"（丢失了 "2" 和第二列内容），最终显示在 (5,1) 位置。

## 根因分析

### 数据流
1. PaddleOCR PPStructureV3 输出 HTML 表格字符串
2. `_TableHtmlParser`（paddle_extractor.py:34-78）按 `<td>`/`<th>` 标签切分单元格
3. `_expand_html_table`（paddle_extractor.py:1510-1574）展开为二维矩阵
4. `_compute_table_grid`（paddle_extractor.py:1306-1507）计算网格 bbox
5. `_draw_translated_table`（pdf_generator.py:989-1452）绘制翻译后表格

### 根因
PaddleOCR 的 HTML 输出中，第5行少了一个 `<td>` 边界，导致列0和列1的文本被放在同一个 `<td>` 中。`_TableHtmlParser.handle_data` 无分隔地拼接所有文本：

```python
def handle_data(self, data):
    if self.in_cell:
        self.current_cell += data  # 无分隔拼接
```

日志证据（第234行）：
```
[表格溢出] 单元格 (5,1): 文本='OpenWebText2Outbound Reddit链接...'
```

正常情况下，(5,0) 应为 "OpenWebText2"，(5,1) 应为 "Outbound Reddit链接"。

### 次要问题
翻译后 "OpenWebText2" 变为 "OpenWebText"——LLM 在翻译合并后的文本时，可能将 "2" 误认为是上标/序号而丢弃，或因文本过长被截断。

## What Changes
- 在 `_parse_html_table` 中增加 PaddleOCR HTML 输出验证：检查每行 `<td>` 数量是否等于表头列数
- 在验证失败时，增加 WARNING 日志记录原始 HTML 和解析后的行结构
- 在 `_expand_html_table` 之后增加列数一致性检查：如果某行单元格数少于预期列数，尝试利用 textline 位置信息重新分割被错误合并的单元格
- 增加 PaddleOCR 原始 HTML 的调试日志，便于后续排查

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`（`_TableHtmlParser`、`_parse_html_table`、`_expand_html_table`）
- Affected specs: `fix-page64-table-false-merge`（PyMuPDF 路径的假合并，不同根因）、`fix-page64-table-cell-empty`（LLM OCR 路径的列宽问题，不同根因）

## ADDED Requirements

### Requirement: PaddleOCR HTML 输出验证与修复
系统 SHALL 在解析 PaddleOCR 表格 HTML 后，验证每行的单元格数量是否与表头列数一致。

#### Scenario: 行单元格数少于表头列数
- **WHEN** PaddleOCR 输出的 HTML 中某行的 `<td>` 数量少于表头列数
- **THEN** 系统应记录 WARNING 日志，包含原始 HTML 和该行的解析结果
- **AND** 系统应尝试利用 textline 位置信息将被错误合并的单元格重新分割

#### Scenario: 行单元格数与表头列数一致
- **WHEN** PaddleOCR 输出的 HTML 中每行的 `<td>` 数量与表头列数一致
- **THEN** 正常处理，无需额外操作

### Requirement: PaddleOCR 原始 HTML 调试日志
系统 SHALL 在解析表格 HTML 时记录原始 HTML 字符串，便于排查 PaddleOCR 输出错误。

#### Scenario: 表格 HTML 解析
- **WHEN** 系统解析 PaddleOCR 返回的表格 HTML
- **THEN** 应记录原始 HTML 的前500字符到 DEBUG 日志

### Requirement: 被合并单元格的 textline 位置分割
系统 SHALL 在检测到某行单元格数不足时，利用 OCR textline 的位置信息将错误合并的单元格文本分割到正确的列中。

#### Scenario: textline 位置可用于分割
- **WHEN** 某行的 `<td>` 数量少于预期列数
- **AND** OCR textline 的位置信息可用于判断文本属于哪一列
- **THEN** 系统应将合并文本按 textline 位置分割到对应的列中

#### Scenario: textline 位置不可用
- **WHEN** 某行的 `<td>` 数量少于预期列数
- **AND** OCR textline 位置信息不足以判断文本归属
- **THEN** 系统应保留原始合并文本，记录 WARNING，不进行强制分割
