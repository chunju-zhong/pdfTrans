# 修复 LLM OCR 藏语 bbox 宽度仅页面 1/4 Spec

## Why

第 6 页藏文 PDF 处理时，LLM OCR (Qwen3.7-Plus) 返回的文本框宽度仅约页面宽度的 1/4（实际文本内容占用 ~80% 页面宽度），导致：
1. 翻译文本被压缩到狭窄区域内，排版严重失真
2. 大量文本内容被裁剪或无法正确渲染
3. 目录页的双栏藏文排版完全错乱

**根因已确认**：LLM 视觉模型对藏文文档的页面布局理解不准确，返回的 bbox 仅覆盖了文本行开头的小部分区域，而非完整文本行宽度。这不是坐标转换代码的问题——Qwen3.7-Plus 对英文 PDF 的 bbox 识别完全正确——而是模型对藏文内容的视觉理解局限。

## 根因分析

### 核心问题

| 证据 | 说明 |
|------|------|
| 英文 PDF bbox 正确 | Qwen3.7-Plus 对英文 PDF 返回的 bbox 准确覆盖文本行，坐标转换逻辑无误 |
| 藏文 PDF bbox 仅覆盖 21% 页面宽度 | Bbox [176,85,1234,195] 在 4963px 宽的图像上只占 25% |
| 实际藏文内容覆盖 75%-87% 页面宽度 | 图像分析显示文本从 x=616 延伸到 x=4337 |
| 页面类型 | 第 6 页是嵌入式扫描图像，目录页双栏藏文排版 |

### 两种可能的根因

1. **模型对藏文视觉特征的理解不足**：Qwen3.7-Plus 对藏文音节（以 tsheg「་」分隔）的视觉特征可能产生误判，只识别了每行开头部分音节而非整行。模型可能将藏文音节间的空格误解为不同文本块的边界。

2. **VLM prompt 缺少语言感知**：当前 VLM prompt (`VLM_JSON_SYSTEM_PROMPT`) 是通用的，没有根据 `source_lang` 注入语言特定的引导。

### 代码层面的不足

**VLM prompt 没有注入 `source_lang`**：`_extract_page`（第 288-326 行）构建的 VLM prompt 不包含文档语言的任何信息，即使 `self.source_lang` 已存储在提取器中。藏文等低资源语言的语言提示在 `fix-llm-ocr-tibetan-recognition` 中已添加到 DeepSeek-OCR 路径，但 VLM 路径未覆盖。

### 影响

- 藏文 PDF 的 LLM OCR 处理后，翻译文本被压缩到错误位置
- 目录页等含大量文本的页面显示严重失真

## What Changes

**唯一变更**：VLM prompt 注入 `source_lang`，对藏文增加 bbox 覆盖完整行宽的引导指令。

## Impact

- Affected code:
  - `modules/ocr/llm_extractor.py` — `_extract_page` 中 VLM prompt 构建
- DeepSeek-OCR 路径不受影响（已通过 `fix-llm-ocr-tibetan-recognition` 注入语言信息）
- 英文等其他语言的 LLM OCR 处理无回归

## ADDED Requirements

### Requirement: VLM prompt 注入 source_lang

`_extract_page` SHALL 在 VLM 模型的 user message 中注入源语言信息。当 `source_lang == 'bo'`（藏文）时，增加藏文 OCR 特殊引导。

#### Scenario: Qwen3.7-Plus 处理藏文页面

- **WHEN** 源语言为藏文（`source_lang == 'bo'`）且使用 VLM 模型
- **THEN** user message prompt 包含藏文特别提示，强调：
  - 文档语言是藏文（བོད་སྐད）
  - 每个文本块的 bbox 必须覆盖从最左字符到最右字符的完整行宽
  - 不要因音节分隔符「་」或音节间的空格而将一行文本拆分为多个 bbox

#### Scenario: VLM 模型处理非藏文页面

- **WHEN** 源语言为英文等其他语言
- **THEN** prompt 行为与修改前一致，无回归

## REMOVED Requirements

### Requirement: Y 轴翻转（原 fix-pixel-to-pdf-y-flip spec）

**Reason**: 用户明确指示 LLM OCR 和普通模式都不需要翻转 Y 轴。PDF 的 Y 轴翻转是 PyMuPDF 内部机制，不应在 OCR 坐标转换中额外处理。
**Status**: 还原所有 Y 轴翻转相关代码。

### Requirement: bbox 后处理扩展（本 spec 初版）

**Reason**: 用户要求简化修复方案，仅通过 prompt 注入解决，不加后处理容错。
**Status**: 已移除。
