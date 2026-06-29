# 修复提取阶段无条件清理换行符 Spec

## Why

目录页（如第 12 页）翻译后排版丢失，原本逐行的目录条目被堆成连续文本块：

```
"11. 表示学习与嵌入 259 嵌入简介 260 语义搜索 262 ..."
```

根因的**最早起点在文本提取阶段**，不在翻译或排版阶段。对三条提取路径的完整检查结论：

| 提取路径 | 换行处理 | 是否丢失目录换行 |
|---------|---------|----------------|
| PaddleOCR（[paddle_extractor.py:614-621](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py)） | 一个布局区域内多 textline 用 `\n` 拼接后**无条件** `replace('\n', ' ')` | **是 ✗** |
| 非 OCR / PyMuPDF（[pdf_extractor.py:454-456](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py)） | **无条件** `replace('\n', ' ')` | **是 ✗** |
| LLM OCR（[llm_response_parser.py:258-264](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_response_parser.py)） | **保留换行**，并按 `\n`/`\n\n` 拆分成多个块（line 291 用 `\n'.join` 合并） | **否 ✓ 无需修复** |

1. `PaddleOcrExtractor._build_text_from_textlines`（[modules/ocr/paddle_extractor.py:614-621](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py)）先按 textline 的 y 坐标分行，用 `\n` 拼接（`result = '\n'.join(lines)`），随后**无条件**执行 `result.replace('\n', ' ')`，把块内所有换行变成空格。该方法签名保留了 `is_title` 参数，但 docstring 注明"保留参数（不再使用）"——原本设计是仅对标题类清理换行，后被改为对所有文本无条件清理，误伤目录、列表、多行正文。
2. `pdf_extractor.py:454-456`（[modules/pdf_extractor.py](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py)）同样无条件 `text_block.block_text.replace('\n', ' ')`。
3. LLM OCR 路径（[llm_response_parser.py](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_response_parser.py)）保留换行并按换行拆块，不存在此问题，无需改动。
4. 目录页的多个目录行（每行是一个 textline 或一组 textline）在 PaddleOCR / 非 OCR 两条路径的提取阶段被合并成空格分隔的连续文本，换行在此丢失。后续翻译 prompt、`split_translated_result`、`format_blocks` 都在此之后运行，无法恢复。
5. **表格单元格检查结论**：[coordinate_utils.py:390](file:///Users/chunju/work/pdfTrans/modules/extractors/coordinate_utils.py)（`create_pdf_cell`）与 [llm_table_parser.py:235](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_table_parser.py) 的 `replace('\n', ' ')` 针对**单个表格单元格（PdfCell）**。表格单元格在渲染时需保持单行，多行会破坏表格布局，因此清理换行**合理且必要**，与目录（多行结构化文本需保留换行）是不同场景，**不纳入本次修复范围**。

历史背景：`centralize-newline-cleanup-at-extraction` spec 将换行清理"统一"到提取阶段以解决标题渲染问题（标题含换行导致截断），但实现变成了无条件清理所有文本，过度修复误伤了目录/列表/多行结构化文本。本 spec 恢复"按文本类型区分"的清理策略。

## What Changes

- **核心修复**：`_build_text_from_textlines` 恢复 `is_title` 参数的作用——仅当 `is_title=True` 时清理换行符（标题保持单行），`is_title=False` 时保留 `\n`（目录/列表/正文保留多行结构）。调用处 [paddle_extractor.py:805](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py) 与 [paddle_extractor.py:950](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py) 已传 `is_title=(label in self.TITLE_LABELS)`，无需改动。
- **pdf_extractor 同步**：`pdf_extractor.py:454-456` 区分标题与正文，仅对标题类文本清理换行，正文/目录/列表保留换行。需确认 `pdf_extractor` 是否有标题类型判断；若无，按 `block_type` 或文本特征区分。
- **保留标题清理行为**：标题类文本（`paragraph_title`/`title`/`section_title`/`document_title`/`doc_title`）仍清理换行，确保标题单行，不回退历史 spec `restore-newline-cleanup-in-text-extraction` 解决的标题渲染问题。
- 不改动翻译 prompt `_generate_system_prompt`、排版 prompt `_FORMAT_SYSTEM_PROMPT`（由现有 spec `fix-format-prompt-toc-line-collapse` 处理，作为次要保护层）。
- 不改动 `split_translated_result` 的按长度切分逻辑。
- 不改动 PaddleOCR 的标签识别（目录被识别为何种标签不在本次范围；若目录被误识别为标题类，需另行处理）。

## Impact

- Affected specs:
  - `fix-format-prompt-toc-line-collapse`（互补：本 spec 修提取阶段根因，该 spec 修翻译/排版 prompt 作为次要保护）
  - `centralize-newline-cleanup-at-extraction`（本 spec 修正其过度修复：从无条件清理改为按类型区分）
  - `restore-newline-cleanup-in-text-extraction`（本 spec 保留其对标题清理的行为，不回退）
- Affected code:
  - [modules/ocr/paddle_extractor.py](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py) — `_build_text_from_textlines` 方法（line 614-621）
  - [modules/pdf_extractor.py](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py) — 换行清理逻辑（line 454-456）
- 行为变更：非标题类文本块（目录、列表、多行正文）在提取阶段保留换行符；标题类文本仍清理换行符保持单行。
- 风险：需确认渲染层是否能正确处理含 `\n` 的文本块（历史清理换行可能是为了规避渲染问题）；若渲染层有依赖单行文本的逻辑，需同步适配。

## ADDED Requirements

### Requirement: 提取阶段按文本类型区分清理换行符

文本提取阶段 SHALL 按文本类型区分换行符清理策略：标题类文本清理换行符保持单行；非标题类文本（目录、列表、多行正文）保留换行符以维持多行结构。

#### Scenario: 目录块保留换行
- **WHEN** 提取一个包含多行目录条目的非标题类文本块（如目录页的目录行）
- **THEN** 提取后的 `block_text` 保留每个目录行之间的 `\n`
- **AND** 不将 `\n` 替换为空格或合并为连续段落

#### Scenario: 多行正文保留换行
- **WHEN** 提取一个包含多个自然段或多行的非标题类正文块
- **THEN** 提取后的 `block_text` 保留原有的 `\n` 换行结构

#### Scenario: 标题块仍清理换行
- **WHEN** 提取一个标题类文本块（`paragraph_title`/`title`/`section_title`/`document_title`/`doc_title`）
- **THEN** 提取后的 `block_text` 清理换行符（`\n` 替换为空格或移除），保持单行
- **AND** 与历史 spec `restore-newline-cleanup-in-text-extraction` 的行为一致

#### Scenario: pdf_extractor 区分标题与正文
- **WHEN** `pdf_extractor` 提取文本块
- **THEN** 仅对标题类文本清理换行符
- **AND** 正文/目录/列表保留换行符

## MODIFIED Requirements

### Requirement: _build_text_from_textlines 换行清理逻辑

`_build_text_from_textlines`（[modules/ocr/paddle_extractor.py:575-623](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py)）修改：

1. 恢复 `is_title` 参数的作用：当前 docstring 标注"保留参数（不再使用）"，实际应恢复为控制换行清理的开关。
2. 现状（line 616-621）：
   ```python
   # 统一删除换行符
   if result and '\n' in result:
       original_text = result
       result = result.replace('\n', ' ')
       newline_count = original_text.count('\n')
       logger.info(f"[换行符清理] 文本删除换行符: ...")
   ```
3. 修改为：仅当 `is_title=True` 时执行换行清理；`is_title=False` 时保留 `result` 的 `\n` 不变。
4. 调用处 [paddle_extractor.py:805](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py) 与 [paddle_extractor.py:950](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py) 已正确传递 `is_title=(label in self.TITLE_LABELS)`，无需改动。

### Requirement: pdf_extractor 换行清理逻辑

`pdf_extractor.py:454-456`（[modules/pdf_extractor.py](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py)）修改：

1. 现状（无条件清理）：
   ```python
   if '\n' in text:
       text_block.block_text = text_block.block_text.replace('\n', ' ')
   ```
2. 修改为：仅对标题类 `block_type` 清理换行符，非标题类保留换行。需确认 `pdf_extractor` 中 `block_type` 的取值与标题判断方式。

## REMOVED Requirements

无删除项。保留历史 spec 对标题清理换行的行为，仅恢复"按类型区分"的策略。
