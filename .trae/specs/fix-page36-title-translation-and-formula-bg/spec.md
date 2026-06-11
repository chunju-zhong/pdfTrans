# 修复36页标题翻译和表格识别、38页公式背景覆盖 Spec

## Why

最新运行日志显示三个问题：1）36页标题"Oxygen transfer efficiency"被识别为 `header` 标签，`is_body_text=False`，导致不参与翻译；2）36页表格区域被版面分析识别为 `chart`/`image` 而非 `table`，跳过表格识别流程；3）38页公式已能正确渲染为图片，但公式区域原文背景未被白色矩形覆盖，导致原文和公式图片重叠。

## What Changes

- **修复 `header` 标签的翻译逻辑**：将 `header` 从 `NON_BODY_LABELS` 中移除，或将 `header` 标签中字体较大的标题类文本纳入翻译范围
- **修复公式渲染时原文背景覆盖**：在 `insert_image` 之前先绘制白色背景矩形
- **表格识别**：36页表格区域被识别为 `chart`/`image` 而非 `table`，这是 PP-StructureV3 版面分析模型的识别结果，当前无法通过代码修改解决

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`（`NON_BODY_LABELS` 定义）、`modules/pdf_generator.py`（公式背景覆盖）、`services/translation_service.py`（翻译过滤逻辑）

## ADDED Requirements

### Requirement: header 标签中的标题文本应参与翻译

`header` 标签的文本不应一律排除在翻译之外。当 `header` 标签的文本是页面主标题（如 "Oxygen transfer efficiency"）时，应参与翻译。

#### Scenario: header 标签标题翻译

- **WHEN** OCR 版面分析返回 `label='header'` 且文本内容为页面主标题（字体较大、位于页面顶部）
- **THEN** 该文本块 `is_body_text=True`，参与翻译

#### Scenario: header 标签页眉不翻译

- **WHEN** OCR 版面分析返回 `label='header'` 且文本内容为重复出现的页眉（如公司名、文档编号）
- **THEN** 该文本块 `is_body_text=False`，不参与翻译

### Requirement: 公式渲染前覆盖原文背景

公式以图片形式插入 PDF 时，应先绘制白色背景矩形覆盖原文，再插入公式图片，避免原文与公式图片重叠。

#### Scenario: 公式图片插入前覆盖原文

- **WHEN** 翻译后的文本块 `is_formula=True` 且公式图片渲染成功
- **THEN** 在 `insert_image` 之前，先在公式区域绘制白色填充矩形覆盖原文

## MODIFIED Requirements

### Requirement: NON_BODY_LABELS 分类

`NON_BODY_LABELS` 应仅包含真正的非内容性标签（如 `page_number`），而 `header` 和 `paragraph_title` 应根据上下文判断是否为正文。

当前 `NON_BODY_LABELS = {'header', 'footer', 'page_number', 'footnote', 'paragraph_title'}`

修改策略：将 `header` 从 `NON_BODY_LABELS` 移除。PP-StructureV3 将页面主标题标记为 `header`，这些标题应参与翻译。真正的页眉/页脚会通过 `text_analyzer.py` 的页眉页脚检测逻辑另行标记为非正文。

## REMOVED Requirements

（无移除的需求）

## 根因分析详情

### 问题1：36页标题"Oxygen transfer efficiency"没有翻译

**根因**：在 `paddle_extractor.py` 第86行，`NON_BODY_LABELS = {'header', 'footer', 'page_number', 'footnote', 'paragraph_title'}`。标题 "Oxygen transfer efficiency" 被版面分析标记为 `label=header`，在第586-587行被设置 `is_body_text=False`。在 `translation_service.py` 第288行，只有 `is_body_text=True` 的文本块才会被加入翻译列表，因此该标题不参与翻译。

**修改方案**：将 `header` 从 `NON_BODY_LABELS` 中移除。PP-StructureV3 将页面主标题标记为 `header` 是合理的，但这些标题应参与翻译。真正的重复页眉会通过 `text_analyzer.py` 的页眉检测逻辑（基于文本重复出现）另行标记为非正文。

### 问题2：36页表格没有识别

**根因**：PP-StructureV3 版面分析将36页的表格区域识别为 `chart` 和 `image`，而非 `table`。日志显示 `{'chart': 1, 'image': 1, ...}`，没有 `table` 标签。步骤2的表格识别仅在 `has_table=True` 时执行，因此36页跳过了表格识别。

**修改方案**：这是 PP-StructureV3 模型的识别限制。当前无法通过代码修改解决。如果需要，可以考虑：1）将 `chart` 区域也送入表格识别流程；2）对 `chart`/`image` 区域进行独立的 OCR 文本提取。

### 问题3：38页公式原文背景没有覆盖

**根因**：在 `pdf_generator.py` 第242-248行，公式渲染成功后直接调用 `page.insert_image(rect, stream=img_buf.getvalue())` 并 `continue`，跳过了第250-257行的白色背景矩形绘制逻辑。普通文本块会先绘制白色背景矩形（`page.draw_rect(bg_rect, color=(1, 1, 1), fill=True, width=0)`），但公式块在 `continue` 之前没有执行这一步。

**修改方案**：在 `insert_image` 之前，先绘制白色背景矩形覆盖原文。
