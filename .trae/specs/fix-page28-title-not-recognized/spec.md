# 诊断并修复第28页段落标题和英文未被识别翻译 Spec

## Why

OCR翻译20-30页时，第28页第一段标题和英文文本没有被识别并翻译。需要诊断根因并修复。

## 根因分析（最终确认）

通过日志确认的真正根因是 **`rec_text` 字段名拼写错误**。

### 日志证据

```
[FONT_DEBUG] page=28: rec_texts 长度(0) != rec_boxes 长度(49)，textline_texts 为空
```

第599行使用 `rec_text`（单数）获取 OCR 识别文本，但 PaddleX `OCRResult` 的实际字段名是 `rec_texts`（复数）。这导致 `rec_texts` 始终为 `None`，`textline_texts` 始终为空。

### 级联影响

1. `textline_texts` 为空 → `_build_text_from_textlines` 返回 None
2. 回退到 `content`，但 PP-DocLayout-V3 的 `content` 属性经常为空
3. 补充捕获之前要求 `len(textline_texts) > 0`，也不执行
4. 结果：OCR 识别了49个 textline 但文本全部丢失

### 修复

将 `rec_text` 改为 `rec_texts`（与 PaddleX `OCRResult` 的实际字段名一致）。

## What Changes

- **修复 `rec_text` → `rec_texts` 字段名拼写错误**（核心修复）：PaddleX `OCRResult` 使用 `rec_texts`（复数），代码错误地使用了 `rec_text`（单数）
- **将 `header` 从 `NON_BODY_LABELS` 移除**（已完成）：`header` 标签不应在 OCR 层直接标记为非正文
- **实施 `fix-text-analyzer-false-positive-header-footer` spec 的修复**（已完成）：修复 `_add_similar_blocks` 的短文本误判问题
- **修复补充捕获的"已处理"标记逻辑**（已完成）：只将成功创建 TextBlock 的 bbox 标记为"已处理"
- **增加诊断日志**（已完成）：在 OCR 提取阶段记录每个文本块的 `label` 和 `is_body_text` 状态

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`, `modules/extractors/text_analyzer.py`
- 行为变更：`header` 标签的文本块默认为正文（`is_body_text=True`），由 `text_analyzer.py` 统一判断是否为页眉

## ADDED Requirements

### Requirement: header 标签不再在 OCR 层标记为非正文

系统 SHALL 将 `header` 标签从 `NON_BODY_LABELS` 中移除。`header` 标签的文本块默认为正文（`is_body_text=True`），由后续 `text_analyzer.py` 基于多页重复模式判断是否为真正的页眉。

#### Scenario: PP-DocLayout-V3 标记段落标题为 header

- **WHEN** PP-DocLayout-V3 将页面顶部的段落标题标记为 `header` 标签
- **THEN** 该文本块的 `is_body_text=True`（默认值）
- **AND** 后续由 `text_analyzer.py` 判断是否为真正的页眉

#### Scenario: PP-DocLayout-V3 标记真正的页眉为 header

- **WHEN** PP-DocLayout-V3 将重复出现的页眉标记为 `header` 标签
- **THEN** 该文本块的 `is_body_text=True`（OCR层不拦截）
- **AND** `text_analyzer.py` 基于多页重复模式将其标记为非正文

### Requirement: 修复 _add_similar_blocks 短文本误判

系统 SHALL 修复 `text_analyzer.py` 的 `_add_similar_blocks` 函数，增加文本长度条件避免短文本误判为页眉页脚。

#### Scenario: 短文本相似但不是页眉页脚

- **WHEN** 两个文本块长度均<20个字符且相似度≥90%但<100%
- **THEN** 不应标记为非正文

#### Scenario: 短文本完全相同且为页眉

- **WHEN** 两个文本块长度均<20个字符且完全相同（相似度=100%）
- **THEN** 标记为非正文（当前行为不变）

### Requirement: OCR 提取阶段增加 label 诊断日志

系统 SHALL 在 `_process_page_layout` 中为每个创建的文本块记录 `label` 和 `is_body_text` 状态，便于排查文本块被跳过的原因。

#### Scenario: 文本块创建时记录诊断信息

- **WHEN** OCR 提取创建文本块
- **THEN** 日志中包含该文本块的 `label`、`is_body_text` 和文本预览

### Requirement: 修复 rec_texts 长度不匹配时的级联失败

系统 SHALL 在 `rec_texts` 与 `rec_boxes` 长度不匹配时，仍能从 LayoutBlock 的 `content` 属性提取文本，而非完全跳过该块。

#### Scenario: rec_texts 长度不匹配且 content 有值

- **WHEN** `overall_ocr_res` 的 `rec_texts` 长度与 `rec_boxes` 不匹配
- **AND** LayoutBlock 的 `content` 属性有值
- **THEN** 系统应使用 `content` 作为文本来源创建 TextBlock
- **AND** 使用 LayoutBlock 的 bbox 进行坐标转换和字体估算

#### Scenario: rec_texts 长度不匹配且 content 为空

- **WHEN** `overall_ocr_res` 的 `rec_texts` 长度与 `rec_boxes` 不匹配
- **AND** LayoutBlock 的 `content` 属性为空
- **THEN** 系统应记录 WARNING 日志，说明该块文本提取失败
- **AND** 该块的 bbox 不应阻止补充捕获机制

### Requirement: 补充捕获不依赖 textline_texts

系统 SHALL 在 `textline_texts` 为空但 `textline_boxes` 非空时，仍执行补充捕获。补充捕获应使用 LayoutBlock 的 `content` 作为文本来源。

#### Scenario: textline_texts 为空但有 textline_boxes

- **WHEN** `textline_texts` 为空但 `textline_boxes` 非空
- **THEN** 补充捕获仍应执行
- **AND** 对于未被 LayoutBlock 覆盖的 textline 区域，使用 `content` 或标记为需要人工检查

### Requirement: 只将成功创建 TextBlock 的 bbox 标记为已处理

系统 SHALL 只将成功创建了 TextBlock 的 LayoutBlock bbox 标记为"已处理"，避免空文本块的 bbox 阻止补充捕获。

#### Scenario: LayoutBlock 检测到但文本为空

- **WHEN** PP-DocLayout-V3 检测到一个 LayoutBlock 但文本为空（content 为空且 textline 匹配失败）
- **THEN** 该 LayoutBlock 的 bbox 不应被标记为"已处理"
- **AND** 补充捕获机制仍可覆盖该区域

## MODIFIED Requirements

### Requirement: NON_BODY_LABELS 集合

`NON_BODY_LABELS` SHALL 不包含 `header`，仅保留 `{'footer', 'page_number', 'footnote'}`。

## REMOVED Requirements

（无移除的需求）
