# PaddleOCR 表格内容被 supplement TextBlock 重复提取导致不显示 Spec

## Why
PaddleOCR 识别的第64页表格中，大量单元格内容在输出 PDF 中不显示或溢出。经日志分析，真正根因不是 `estimated_lines` 缺失，而是**表格内容被重复提取了两次**：

1. PaddleOCR 版面分析正确检测到表格区域（bbox [118,313,717,705]），解析 HTML 得到 9 个单元格
2. 但表格的 bbox **未被加入 `processed_pixel_bboxes`**（第868-869行仅设 `has_table=True`，不记录 bbox）
3. 表格内的 73 个 textline 在补充捕获阶段被判定为"未被覆盖"，创建了 20 个 supplement TextBlock
4. 这些 supplement TextBlock 的坐标完全在表格 bbox 内部，与表格单元格重叠
5. 渲染时：文本块先渲染 supplement TextBlock → 表格 redaction 涂黑该区域（误删已渲染的翻译文本）→ 表格单元格渲染翻译文本
6. 最终结果：supplement TextBlock 的翻译文本被表格 redaction 误删，表格单元格的翻译文本因空间不足被截断

## 日志证据

```
# 表格被正确识别
[TABLE_DEBUG] page=64: 表格0提取成功, cells=9, html长度=1423

# 但73个textline未被覆盖，变成20个supplement TextBlock
[SUPPLEMENT] page=64: 发现 73 个未被 LayoutBlock 覆盖且有文本的 textline
[SUPPLEMENT] page=64: 共创建 20 个补充 TextBlock

# supplement TextBlock坐标在表格bbox内部
# 表格PDF坐标=(70.8, 187.7, 430.2, 422.8)
# supplement TextBlock 1: pdf_bbox=(73.8, 190.1, 421.8, 202.1) ← 在表格内

# 渲染时大量溢出（supplement TextBlock高度仅~10pt，翻译后中文更宽）
[WARN] 文本溢出，返回值: -1.9502873909224832，文本框: Rect(74.4, 238.7, 417.6, 248.9)

# 表格单元格也有3个溢出被截断
[表格溢出] 单元格 (1,5): 文本='T5, FLAN-T5, UL2, Llama, 等...', 处理方式=截断
[表格溢出] 单元格 (2,1): 文本='Common Crawl、PubMed Central...', 处理方式=截断
[表格溢出] 单元格 (3,5): 文本='Red Pajama-INCITE, MPT...', 处理方式=截断
```

## What Changes
- 在 PaddleOCR `_process_page_layout()` 中，当处理 `label == 'table'` 时，将表格的像素 bbox 加入 `processed_pixel_bboxes`，使表格内的 textline 不再被判定为"未覆盖"
- 同时为 PaddleOCR 表格单元格设置 `estimated_lines`（参照 LLM OCR 方案），优化绘制阶段的字体大小选择

## Impact
- Affected code: `modules/ocr/paddle_extractor.py` 第868-869行（表格 bbox 未加入 processed_pixel_bboxes）
- Affected code: `modules/ocr/paddle_extractor.py` `_compute_table_grid()` 方法（estimated_lines 缺失）
- Affected code: `modules/pdf_generator.py` `_draw_translated_table()` 方法（estimated_lines > 0 时已有优化逻辑）
- 影响范围：所有 PaddleOCR 识别的表格

## ADDED Requirements

### Requirement: 表格 bbox 加入 processed_pixel_bboxes
PaddleOCR `_process_page_layout()` 中，当 `label == 'table'` 时 SHALL 将表格的像素 bbox 加入 `processed_pixel_bboxes`，使表格内的 textline 不再被误判为"未覆盖"。

#### Scenario: 表格 bbox 加入覆盖列表
- **WHEN** `_process_page_layout()` 遍历 `parsing_res_list` 遇到 `label == 'table'` 的 block
- **THEN** 除了设置 `has_table = True`，还应将 `(x1, y1, x2, y2)` 像素坐标加入 `processed_pixel_bboxes`
- **AND** 这确保表格内的 textline 在补充捕获阶段被判定为"已覆盖"，不会创建重复的 supplement TextBlock

#### Scenario: 表格提取失败时仍加入 bbox
- **WHEN** 表格 HTML 解析失败（如 `table_res_list` 为空或解析异常）
- **THEN** 仍应将表格 bbox 加入 `processed_pixel_bboxes`，防止表格区域的 textline 被重复捕获为 supplement TextBlock

### Requirement: PaddleOCR 表格单元格设置 estimated_lines
PaddleOCR 的 `_compute_table_grid()` 方法 SHALL 为每个有文本的单元格计算并设置 `estimated_lines` 字段，使绘制阶段的字体优化逻辑生效。

#### Scenario: 基于 textline 高度估算字体大小
- **WHEN** `_compute_table_grid()` 收集到 textline 数据
- **THEN** 系统应从 textline bbox 高度估算字体大小：`font_size = textline_height * 0.75`
- **AND** 若某行有多个 textline，取中位数作为该行的字体大小估算
- **AND** 若无 textline 数据，默认 `font_size = 9.0`

#### Scenario: 基于文本内容和列宽计算 estimated_lines
- **WHEN** 列宽已计算完成
- **THEN** 对每个有文本的单元格：
  1. 使用 `_estimate_text_display_width()` 估算文本显示宽度
  2. `span_width = sum(col_widths[col_idx:col_idx + col_span])`
  3. `estimated_lines = max(1, ceil(display_width / span_width))` 当 `span_width > 0`
  4. 将 `estimated_lines` 写入 `cell.estimated_lines`
- **AND** 空单元格的 `estimated_lines` 设为 0

### Requirement: 提取 _estimate_text_display_width 为共享工具函数
`_estimate_text_display_width()` SHALL 从 `llm_extractor.py` 提取到共享模块，供 PaddleOCR 和 LLM OCR 共同使用。

#### Scenario: 共享函数位置
- **WHEN** 两个 OCR 提取器都需要估算文本显示宽度
- **THEN** `_estimate_text_display_width()` 应放在 `modules/extractors/coordinate_utils.py` 中
- **AND** `llm_extractor.py` 和 `paddle_extractor.py` 均从该模块导入

## MODIFIED Requirements

### Requirement: PaddleOCR _compute_table_grid 返回值
原有返回值 `(cells, row_heights, col_widths)` 不变，但 cells 中每个 PdfCell 的 `estimated_lines` 字段现在会被正确设置（之前始终为 0）。
