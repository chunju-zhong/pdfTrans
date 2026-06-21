# 诊断 DeepSeek-OCR 多 bbox 丢失导致原文显示 Spec

## Why

一段英文段落（含跨行断词 `his‐ torical`、`para‐ digm`、`dis‐ crete`）在翻译输出中原文直接显示，看起来像没有翻译。经查日志和输出结果，该段落实际已被翻译，但与上一段被合并显示在一起。根因是 DeepSeek-OCR 在同一个 `<|ref|>` 块中返回了两组 `<|det|>` 坐标（对应两个段落），但 `_parse_det_bbox` 只取了前4个数字（第一个段落的 bbox），第二个段落的 bbox 被丢弃，导致第二个段落区域无 redaction 覆盖，原文直接露出。

## What Changes

- **修复 `_parse_det_bbox` 支持多 bbox 解析**：解析 `<|det|>` 中的所有 bbox 坐标组，而非只取前4个数字
- **拆分多段落 `<|ref|>` 块**：当 `<|det|>` 包含多个 bbox 时，按段落拆分 `actual_text` 为多个 TextBlock，每个使用对应的 bbox
- **新增跨行断词预处理**：在文本提取阶段修复 `his- torical` → `historical` 等断词

## Impact

- Affected code: `modules/ocr/llm_extractor.py`（`_parse_det_bbox` 和 `_parse_ref_tags_response` 方法）、`utils/text_processing.py`（跨行断词修复）
- 影响范围：所有使用 DeepSeek-OCR 提取模式的 PDF 翻译

## 根因分析

### 事实

1. 用户使用 **DeepSeek-OCR-2** 模型（LLM OCR 提取模式），**未开启语义合并**
2. DeepSeek-OCR 返回的 `<|ref|>` 块包含两组 `<|det|>` 坐标：
   ```
   <|ref|>text<|/ref|><|det|>[[135, 80, 861, 175], [264, 197, 790, 391]]<|/det|>
   ```
   第一组 `[135, 80, 861, 175]` 对应上一段，第二组 `[264, 197, 790, 391]` 对应本段
3. `_parse_det_bbox` 使用 `re.findall(r'[\d.]+', det_content)[:4]`，只取前4个数字 → 返回 `(135, 80, 861, 175)`
4. 第二组 bbox `[264, 197, 790, 391]` 被完全丢弃
5. 两个段落被创建为单个 TextBlock，bbox 仅为第一段的区域
6. 翻译后 redaction 只覆盖第一段区域 → 第二段原文直接露出

### 根因链条

```
DeepSeek-OCR 返回 <|ref|> 块含两组 <|det|> 坐标
→ _parse_det_bbox 只取前4个数字（第一段 bbox）
→ 第二段 bbox 丢失
→ 两段文本合并为单个 TextBlock（bbox 仅覆盖第一段区域）
→ 翻译后 redaction 只覆盖第一段区域
→ 第二段原文直接露出
```

### 关键代码

[llm_extractor.py:536-547](file:///Users/chunju/work/pdfTrans/modules/ocr/llm_extractor.py#L536-L547) — `_parse_det_bbox` 只取前4个数字：

```python
def _parse_det_bbox(self, det_content):
    coords = re.findall(r'[\d.]+', det_content)
    if len(coords) >= 4:
        return tuple(float(c) for c in coords[:4])  # 只取第一组！
    return (0, 0, 0, 0)
```

## ADDED Requirements

### Requirement: `_parse_det_bbox` 支持多 bbox 解析

系统 SHALL 解析 `<|det|>` 标签中的所有 bbox 坐标组，返回列表而非单个元组。

#### Scenario: `<|det|>` 包含两组坐标

- **WHEN** `<|det|>` 内容为 `[[135, 80, 861, 175], [264, 197, 790, 391]]`
- **THEN** 系统返回 `[(135, 80, 861, 175), (264, 197, 790, 391)]`

#### Scenario: `<|det|>` 包含一组坐标

- **WHEN** `<|det|>` 内容为 `[[135, 80, 861, 175]]`
- **THEN** 系统返回 `[(135, 80, 861, 175)]`

#### Scenario: `<|det|>` 为空或格式错误

- **WHEN** `<|det|>` 内容无法解析
- **THEN** 系统返回 `[(0, 0, 0, 0)]`

### Requirement: 多 bbox `<|ref|>` 块按段落拆分为多个 TextBlock

系统 SHALL 在 `_parse_ref_tags_response` 中，当 `<|det|>` 包含多个 bbox 时，将 `actual_text` 按段落拆分（以 `\n\n` 为分隔符），每个段落创建独立的 TextBlock，使用对应的 bbox。

#### Scenario: 两组 bbox + 两段文本

- **WHEN** `<|det|>` 包含2组坐标，`actual_text` 包含2个以 `\n\n` 分隔的段落
- **THEN** 系统创建2个 TextBlock，第一个使用 bbox1，第二个使用 bbox2

#### Scenario: bbox 数量与段落数量不匹配

- **WHEN** `<|det|>` 包含2组坐标，但 `actual_text` 只有1个段落
- **THEN** 系统创建1个 TextBlock，使用第一个 bbox（回退策略）

#### Scenario: 单 bbox + 单段落

- **WHEN** `<|det|>` 包含1组坐标，`actual_text` 为1个段落
- **THEN** 系统创建1个 TextBlock，保持现有行为

### Requirement: 跨行断词预处理

系统 SHALL 在文本提取阶段检测并修复跨行断词。当文本中出现 `<字母>- <小写字母>` 模式时，应将连字符和空格移除，合并为一个完整单词。

#### Scenario: 修复跨行断词

- **WHEN** 提取的文本包含模式 `his- torical`
- **THEN** 系统将其修复为 `historical`

#### Scenario: 保留合法连字符

- **WHEN** 提取的文本包含 `next-token`（连字符后无空格）
- **THEN** 系统保留原样，不做修改
