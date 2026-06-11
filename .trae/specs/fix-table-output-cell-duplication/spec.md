# 修复表格最后一行 Output 单元格翻译内容重复 Spec

## Why

第20页表格最后一行，第一列 "Output" 被翻译成了 JSON 内容（与第二列重复），应该保留为 "Output" 或翻译为 "输出"。根因是 `translate_table_row` 用 `\n|||` 分隔符将同行多个单元格拼接后一起翻译，LLM 翻译时未正确保留分隔符，导致拆分后单元格内容错位。

## What Changes

- 在翻译 prompt 中增加规则：当输入包含 `|||` 分隔符时，翻译结果必须保留每个分隔符，且每个分隔段独立翻译不合并
- 增加 fallback：当 `split(SEPARATOR)` 结果数量不匹配时，逐个单元格单独翻译

## Impact

- Affected code: `modules/translator.py`（system prompt）、`services/translation_service.py`（`translate_table_row` fallback）

## ADDED Requirements

### Requirement: 翻译 prompt 保留单元格分隔符

当表格行翻译输入包含 `\n|||` 分隔符时，LLM SHALL 在翻译结果中保留每个分隔符，且每个分隔段独立翻译不合并。

#### Scenario: 输入包含分隔符

- **WHEN** 翻译输入包含 `\n|||` 分隔符（表示多个单元格文本）
- **THEN** LLM 在翻译结果中保留每个 `\n|||` 分隔符
- **AND** 每个分隔段独立翻译，不将相邻段的内容合并
- **AND** 短文本段（如 "Output"）保持为对应语言的翻译（如 "输出"），不与相邻段合并

#### Scenario: 翻译后分隔符数量不匹配

- **WHEN** 翻译后 `split("\n|||")` 得到的部分数少于原始单元格数
- **THEN** 对缺失的部分逐个单元格单独翻译作为 fallback
- **AND** 记录警告日志

## MODIFIED Requirements

### Requirement: translator.py system prompt 增加分隔符规则

在 `_generate_system_prompt` 的规则列表中新增：

```
17. **保留单元格分隔符**：当输入文本包含 "|||" 分隔符时，这是表格单元格之间的分隔标记。你必须在翻译结果的对应位置保留每个 "|||" 分隔符，且每个分隔段独立翻译，绝不将相邻段的内容合并或混入其他段。短文本段（如标签词）保持为对应语言的翻译，不与相邻段合并。
```

### Requirement: translate_table_row 增加 fallback

当 `split(SEPARATOR)` 结果数量与原始单元格数量不匹配时：

```python
parts = translated.split(SEPARATOR)
if len(parts) != len(non_empty_cells):
    logger.warning(f"表格行翻译分隔符不匹配: 期望{len(non_empty_cells)}段, 实际{len(parts)}段, 回退到逐个翻译")
    # 逐个单元格翻译作为 fallback
    result = {}
    for col_idx, text in non_empty_cells:
        cell = row_cells[col_idx]
        try:
            single_result = translator.translate(text, source_lang, target_lang, doc_type=doc_type, glossary=glossary)
            result[col_idx] = PdfCell(text=single_result.content.strip(), bbox=cell.bbox, ...)
        except:
            result[col_idx] = PdfCell(text=text, bbox=cell.bbox, ...)
    return table_idx, row_idx, result, table_pages.get(table_idx, 0)
```

## REMOVED Requirements

无
