# 分析36页和38页问题 Spec

## Why

用户反馈两个问题：1）36页标题"Oxygen transfer efficiency"和表格内容未正确识别和翻译；2）38页公式输出不正确，公式下方文字未识别和翻译。需要从运行日志中定位根因并提出修改方案。

## What Changes

- **分析日志，定位根因**（不修改代码，仅分析问题）
- **提出修改方案**

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`, `modules/pdf_generator.py`

## 问题1：36页标题"Oxygen transfer efficiency"和表格内容未识别/翻译

### 根因分析

从日志（最后一次运行，约18:02）可见：

1. **标题"Oxygen transfer efficiency"被正确识别**：
   - `[FONT_DEBUG] page=36, label=header, is_body=False, text='Oxygen transfer efficiency ', font_size=18.90`
   - 标题被版面分析识别为 `label=header`，这是已知标签，**已成功提取**

2. **"Oxygen transfer efficiency"在PDF渲染阶段出现溢出**：
   - `溢出文本: 'Oxygen transfer efficiency...' (完整长度=26)`
   - 这是渲染阶段的警告，**不代表未识别**，而是翻译后文本在PDF中渲染时出现框溢出

3. **表格内容**：
   - `[LAYOUT_DEBUG] page=36: {'chart': 1, 'footer': 1, 'header': 1, 'image': 1, 'paragraph_title': 1, 'text': 3, 'vision_footnote': 1}, text_blocks=7, image_regions=2`
   - `OCR提取完成: 共2页, 0个表格` — **没有检测到表格**
   - 36页没有 `label=table`，说明PP-StructureV3版面分析未将该区域识别为表格，而是识别为 `image` 或 `chart`
   - 此外 `OCR_SKIP_TABLE=False` 已设置，但 `use_table=False` 是因为该页确实没有检测到 `label=table`

4. **`paragraph_title` 标签问题**：
   - 36页有 `paragraph_title` 标签（内容 'SETAS'），这个标签已在 `TEXT_LABELS` 中，但也被列在 `NON_BODY_LABELS` 中
   - 它**不是未知标签**，会被正常处理，只是不参与正文标记

5. **`vision_footnote` 是未知标签**：
   - `[LABEL_DEBUG] page=36: unknown label='vision_footnote', content_preview='Christensson,2013'`
   - 该标签不在 `TEXT_LABELS` 中，**会走到 else 分支被当作普通文本处理**（第623-647行），不会丢失

### 结论

- **标题"Oxygen transfer efficiency"已被正确识别**，不存在识别问题
- 表格内容**未被识别为表格**（版面分析将其识别为 chart/image），所以没有走表格识别流程
- PDF渲染时的溢出警告是样式适配问题，不影响识别和翻译

### 修改方案

1. **表格识别**：检查36页原PDF，确认该区域是否真的是表格。如果是图片/图表形式的表格，OCR版面分析无法识别为 `table`，需要走图表裁剪+独立OCR流程
2. **溢出问题**：属于渲染适配问题，不是识别问题

## 问题2：38页公式没有正确输出，公式下方文字未识别和翻译

### 根因分析

1. **公式被正确检测到**：
   - `[LAYOUT_DEBUG] page=38: {'footer': 1, 'formula': 1, 'paragraph_title': 2, 'text': 5}, text_blocks=9, image_regions=0`
   - 有 `formula: 1`，说明版面分析检测到了公式区域

2. **公式渲染失败**：
   - `公式渲染失败，降级为文本: No module named 'matplotlib'`
   - **根因：环境中缺少 matplotlib 模块**，导致公式无法渲染为图片

3. **公式降级为文本后溢出被截断**：
   - `溢出文本: 'SOTR{ = }\frac{f_{\mathrm{d}}...' (完整长度=292)`
   - `截断文本后渲染成功: 原始长度=292, 截断后长度=149, 截断比例=50%`
   - 由于缺少matplotlib，公式被当作LaTeX文本渲染，292字符的LaTeX公式在PDF框中溢出，最终被截断到149字符

4. **38页OCR文本内容**：
   - 从最新运行（18:09）的 `[FONT_DEBUG]` 日志，page=38 只提取到 5 个 text 块 + 2 个 paragraph_title + 1 个 formula + 1 个 footer
   - 对比之前一次运行（约07:13），旧版版面分析检测到更多文本块（包括 `doc_title`, 更多 `text` 块，如 `α = Grenzflächenfaktor` 等参数说明）
   - **新版版面分析的文本提取结果比旧版少**，部分文本块可能被合并或遗漏

5. **公式下方文字**：
   - 38页的 OCR 提取了 5 个 text 块（'Auslegung der Beluftung Ermitt', 'abSalzgehalten>2gTDS/I...', 'M229/Jardin/29.09.2016', 'Jardin,2016', 等）
   - **公式下方的参数说明文字（如 α, β, fd 等变量说明）未被独立提取为文本块**
   - 在旧版结果中，这些内容被识别为独立 text 块（如 `α = Grenzflächenfaktor 0,3...1`），但新版没有
   - 原因可能是新版版面分析的 block 合并策略不同，或者这些区域被归类为 formula 区域的一部分

### 结论

1. **公式输出不正确**的根因：缺少 `matplotlib` 模块，公式无法渲染为图片，降级为LaTeX文本后被截断
2. **公式下方文字未识别**的根因：新版PP-StructureV3版面分析可能将公式周围的参数说明文字合并或遗漏，没有独立提取为 text 块

### 修改方案

1. **安装 matplotlib**：解决公式渲染问题
2. **检查38页版面分析结果**：确认 `parsing_res_list` 中是否包含公式下方的文字块。如果PP-StructureV3没有检测到，需要在步骤1的 `_process_page_layout` 中增加对 formula 区域周围文本的提取逻辑
3. **对比新旧版面分析差异**：确认是否有模型版本或参数差异导致文本块数量减少
