# 修复表格标题未翻译和文本框/表格框水平padding不足 Spec

## Why

最后一次生成的 PDF 存在两个视觉质量问题：

### 问题1：表格下方文字未翻译

PDF 中表格下方原文 "Table 1: A non-exhaustive example of different categories of actors for authentication" 保持英文未翻译。

**根因分析**：

* PP-StructureV3 版面分析时，该页面的布局统计为 `{'footer': 1, 'header': 1, 'number': 1, 'table': 1, 'text': 2}`，仅检测到 2 个 `text` 标签块

* "Table 1:..."这段文本未被 PP-StructureV3 识别为独立的 `text` 或 `table_caption` 标签块

* 该文本位于表格 bbox 附近（可能在 bbox 内），但不在 `_parse_html_table` 从表格 HTML 解析出的单元格内容中

* PP-StructureV3 的 `parsing_res_list` 没有为这段文字返回独立的 LayoutBlock，导致系统完全无法获取这段文字

* 系统流程中，只有 `parsing_res_list` 中的 `text`/`title`/`table_caption` 等标签块才会被提取并翻译，PP-StructureV3 漏检的文本无法被捕获

### 问题2：文本框和表格框偏小，右侧边缘残留原文

OCR 识别到的文本框和表格框都偏小，白色背景没有完全覆盖原文本/表格，右侧边缘有残留原文露出。

**根因分析**：

* `pdf_generator.py` 第242-249行，绘制覆盖原文的白色背景时，只添加了垂直方向的 padding，未添加水平方向的 padding

* 当前 `bg_padding = original_font_size` 的设计过于粗糙：`original_font_size` 在 6-12pt 范围时，padding 为 6-12pt，对于水平方向来说过大，可能压到相邻列或图文

* PP-StructureV3 返回的 bbox 是版面区域的紧密边界框，紧贴文字边缘，没有多余边距

* 非 OCR 模式下 PyMuPDF `get_text("blocks")` 返回的 bbox 包含完整文本块区域（含边距），所以不存在此问题

* 表格单元格的白色背景绘制（第610行）同样没有水平 padding，导致表格框右侧也可能露出原文

## What Changes

### 变更1：PP-StructureV3 漏检文本的通用捕获机制

**当前漏洞分析**：PP-StructureV3 对特定页面区域可能不生成 LayoutBlock（如表格周边的标题/脚注），或使用非文本标签（如 `figure_caption` 在 IMAGE\_LABELS 中导致文本丢失）。现有系统只处理 `parsing_res_list` 中已有标签的块，漏检文本完全不可见。

**解决方案**（分为两个子变更）：

**变更1a：基于** **`overall_ocr_res`** **的通用 textline 覆盖检测**

* 在 `paddle_extractor.py` 的 `_process_page_layout` 方法末尾，对所有 `parsing_res_list` 处理的 LayoutBlock 收集其 bbox 集合

* 遍历 `overall_ocr_res` 的 textline 数据，对每一个 textline，检查其中心点是否落在 **任何一个已处理的 LayoutBlock bbox 内**

* 未被任何 LayoutBlock 覆盖的 textline，聚合成文本块，创建为独立的 `TextBlock` 加入翻译队列

* 此方案自动覆盖：表格标题/脚注、图表标题、边注、及其他 PP-StructureV3 未分配 LayoutBlock 的任何文本

* 设定合理的"未覆盖判定"阈值：textline 中心点必须不落在任何 processed\_block\_like（已处理文本/表格/公式/图像块）的 bbox 扩展范围内

**变更1b：`figure_caption`** **标签的文本提取**

* 当前 `figure_caption` 在 `IMAGE_LABELS` 中，文本内容完全丢失

* 在图像处理分支中，为 `figure_caption` 标签额外提取其 textline 级文本（使用 `_build_text_from_textlines`），创建为 `TextBlock` 加入翻译队列

* 或通过变更1a 的通用检测自动捕获 `figure_caption` 区域内的未覆盖 textline

### 变更2：文本框背景 padding 使用合理计算方式

* 当前 `bg_padding = original_font_size` 直接等于字号，对于小字体（6pt）padding 太小，对于大字体（12pt+）又可能压到周围元素

* 改为比例计算 + 上下限限制：`bg_padding = max(3, min(original_font_size * 0.4, 8))`

  * 最小值 3pt：确保即使小字体也有足够覆盖

  * 最大值 8pt：避免大字体 padding 过大

  * 比例 0.4：对于 10pt 正文 = 4pt，合理对称

* `bg_rect` 同时使用水平和垂直 padding，仍然 clamp 到页面范围内

### 变更3：表格单元格背景增加水平 padding

* 在 `pdf_generator.py` 的表格单元格背景绘制逻辑中，为单元格的 `rect` 水平方向添加 padding

* 确保表格框的白色背景能完全覆盖原表格单元格区域

## Impact

* Affected specs: `fix-table-ocr-translation`, `fix-table-bbox-coordinate`, `fix-background-rect-height-too-small`

* Affected code: `modules/ocr/paddle_extractor.py`, `modules/pdf_generator.py`

## ADDED Requirements

### Requirement: PP-StructureV3 漏检文本通用捕获

系统在 OCR 提取完成后，SHALL 使用 `overall_ocr_res` 的 textline 级文本数据检测所有未被 `parsing_res_list` LayoutBlock 覆盖的文本。

#### Scenario: 通用 textline 覆盖检测捕获漏检文本

* **WHEN** `overall_ocr_res` 包含 textline 级文本数据

* **AND** 部分 textline 的中心点未落在任何已处理的 LayoutBlock（text/table/formula/image\_labels 等）的 bbox 扩展范围内

* **THEN** 系统将这些漏检的 textline 按垂直邻近关系聚合成文本块

* **AND** 为每个聚合文本块创建独立的 `TextBlock` 对象（标签为 `supplementary`，block\_type=0）

* **AND** 这些文本块被加入 `text_blocks` 列表参与翻译

#### Scenario: `figure_caption` 标签的文本提取

* **WHEN** `parsing_res_list` 中的 LayoutBlock 标签为 `figure_caption`

* **THEN** 系统使用 `_build_text_from_textlines` 从 `overall_ocr_res` 提取该区域内的 textline 文本

* **AND** 提取的文本创建为 `TextBlock` 加入 `text_blocks` 列表

#### Scenario: 无可用的 overall\_ocr\_res

* **WHEN** `overall_ocr_res` 不可用或无 textline 数据

* **THEN** 跳过漏检文本捕获，保持当前行为

### Requirement: 文本框背景 padding 使用合理计算公式

系统在绘制覆盖原文的白色背景时，SHALL 使用 `max(3, min(original_font_size * 0.4, 8))` 计算 padding 值，并在水平和垂直方向同时应用。

#### Scenario: 小字体文本（如 6pt footer）

- **WHEN** `original_font_size = 6pt`
- **THEN** `bg_padding = max(3, min(2.4, 8)) = 3pt`（确保最小值）

#### Scenario: 正常正文文本（10pt）

- **WHEN** `original_font_size = 10pt`
- **THEN** `bg_padding = max(3, min(4, 8)) = 4pt`（比例合理）

#### Scenario: 大标题文本（20pt）

- **WHEN** `original_font_size = 20pt`
- **THEN** `bg_padding = max(3, min(8, 8)) = 8pt`（上限限制，不压到周围元素）

### Requirement: 表格单元格背景增加水平 padding

系统在绘制表格单元格的白色背景时，SHALL 在水平方向添加 padding。

#### Scenario: 表格单元格背景绘制

* **WHEN** OCR 模式下绘制表格单元格的白色背景（`page.draw_rect(rect, color=(1,1,1), fill=True, width=0)`）

* **THEN** 背景矩形在 X 方向左右各扩展适量 padding（建议 `2pt`，避免扩展到相邻单元格）

* **AND** 单元格边框（`page.draw_rect(rect, color=(0,0,0), width=0.5)`）不受 padding 影响，仍使用原始单元格边界

## MODIFIED Requirements

### Requirement: pdf\_generator.py 文本背景 padding 使用合理计算

修改 `pdf_generator.py` 中 `bg_padding` 的计算逻辑和 `bg_rect` 的水平扩展。

修改前：

```python
bg_padding = original_font_size
bg_rect = fitz.Rect(
    rect.x0,
    max(rect.y0 - bg_padding, 0),
    rect.x1,
    min(rect.y1 + bg_padding, page.rect.height)
)
```

修改后：

```python
bg_padding = max(3, min(original_font_size * 0.4, 8))
bg_rect = fitz.Rect(
    max(rect.x0 - bg_padding, 0),
    max(rect.y0 - bg_padding, 0),
    min(rect.x1 + bg_padding, page.rect.width),
    min(rect.y1 + bg_padding, page.rect.height)
)
```

### Requirement: pdf\_generator.py 表格单元格背景水平扩展

修改 `pdf_generator.py` 中表格单元格白色背景的绘制区域，增加水平 padding。

修改前：

```python
page.draw_rect(rect, color=(1, 1, 1), fill=True, width=0)
```

修改后：

```python
cell_bg_rect = fitz.Rect(
    max(rect.x0 - 2, 0),
    rect.y0,
    min(rect.x1 + 2, page.rect.width),
    rect.y1
)
page.draw_rect(cell_bg_rect, color=(1, 1, 1), fill=True, width=0)
```

（单元格边框不变，仍使用原始 `rect`）

### Requirement: paddle\_extractor.py PP-StructureV3 漏检文本捕获

在 `_process_page_layout` 方法末尾，所有 `parsing_res_list` 处理完成后，执行以下逻辑：

1. 收集所有已处理 LayoutBlock 的 bbox 集合（包括 text、title、table、formula、figure\_caption 等所有已知标签的块）
2. 对 `overall_ocr_res` 中的每个 textline，检查其中心点是否落在任意已处理 bbox 的扩展范围内
3. 未被覆盖的 textline，按垂直邻近关系（Y 差 < 行高）聚合成文本块
4. 为每个聚合块创建 `TextBlock`，设置 `is_body_text=True`，加入 `text_blocks` 列表

同时，在 `figure_caption` 标签的图像处理分支中，添加 textline 文本提取逻辑。当标签为 `figure_caption` 时，使用 `_build_text_from_textlines` 提取文本并创建 `TextBlock`。

## REMOVED Requirements

（无移除的需求）
