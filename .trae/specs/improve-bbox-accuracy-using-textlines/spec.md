# 使用 textline bbox 提升文本框和表格单元格坐标精度 Spec

## Why

当前生成的 PDF 中，文本框和表格框仍然存在右侧边缘/底部残留原文的残影问题。原因是使用的 bbox 精度不足：

**文本块：**
- 当前使用 `block.bbox`（PP-StructureV3 的版面布局区域 bbox）作为文本框位置
- 这个 layout bbox 是版面分析区域，不是实际文字的像素精确边界
- layout bbox 的右/下边界可能比实际文字窄，导致背景矩形覆盖不全，残留原文

**表格单元格：**
- 当前 `_parse_html_table` 将所有单元格 bbox 设为 `(0,0,0,0)`
- PDF 生成时只能通过行列索引计算近似位置，精度有限
- 表格底部边界同样可能不足

**已有但未被利用的精确数据：**

`overall_ocr_res` 中的 `rec_boxes` 包含了 PaddleOCR 返回的**每个文字区域的精确像素坐标**（第519-530行）。当前代码只用它提取文本内容（`_build_text_from_textlines`），**丢弃了坐标信息**。

```
当前数据流：
  rec_boxes (x1,y1,x2,y2) → _build_text_from_textlines 提取文本内容 ✓
                          → 坐标信息被丢弃 ✗

优化数据流：
  rec_boxes (x1,y1,x2,y2) → _build_text_from_textlines 提取文本内容 ✓
                          → compute_tight_bbox() 计算文字精确范围 ✓
```

## What Changes

### 变更1：为文本块计算精确边界框（tight bbox）

在 `paddle_extractor.py` 的文本块处理流程中，对于每个 TEXT_LABELS 块，使用 `textline_boxes` 计算落在该布局区域内的所有 textline 的精确 bbox 并集：

```
tight_bbox = (
    min(textline_x1),  ← 最左边文字的起始
    min(textline_y1),  ← 最上方文字的起始
    max(textline_x2),  ← 最右边文字的结束（关键修复：解决右侧残影）
    max(textline_y2)   ← 最下方文字的结束
)
```

用 tight_bbox 替代原始 `block.bbox` 作为 `pixel_bbox`，再经 `_pixel_to_pdf_coords` 转换后传给 PDF 生成器。

**关键设计点**：只有 `_build_text_from_textlines` 匹配到的 textline 才用于计算 tight bbox，确保 bbox 只包含该文本块实际占用的文字区域。

### 变更2：为表格单元格计算精确边界框

在 `_parse_html_table` 返回单元格后，使用 `textline_boxes` 为每个单元格计算精确 bbox：

1. 将表格总 bbox 按行列比例划分为各单元格的近似区域
2. 在每个近似区域内，找到匹配该单元格文本内容或位置匹配的 textline
3. 计算这些 textline 的 bbox 并集，作为该单元格的精确 bbox
4. 对匹配不到的单元格保留近似划分的 bbox（优于 `(0,0,0,0)`）

### 变更3：精简背景 padding（可选优化）

由于 tight bbox 已经精确覆盖文字像素区域，可以将 background padding 从 `max(3, min(font_size * 0.4, 8))` 调整为更小的值（如 `max(1, min(font_size * 0.15, 4))`），同时不牺牲视觉效果。

## Impact

- Affected specs: `fix-table-caption-missing-and-bbox-hpadding`（本优化可以部分替代 padding 方案）
- Affected code: `modules/ocr/paddle_extractor.py`, `modules/pdf_generator.py`

## ADDED Requirements

### Requirement: 文本块使用 textline bbox 计算精确边界框

系统在提取文本块时，SHALL 使用 `overall_ocr_res` 中的 `rec_boxes` 计算文本块的精确像素边界框。

#### Scenario: 有足够的 textline 数据

- **WHEN** 处理 TEXT_LABELS 中的文本块
- **AND** `textline_boxes` 中有至少一个 textline 落在该布局区域 bbox 内
- **THEN** 系统计算这些 textline 的 bbox 并集作为 tight_bbox
- **AND** 使用 tight_bbox 经 `_pixel_to_pdf_coords` 转换后作为该文本块的 bbox

#### Scenario: textline 数据不足或不可用

- **WHEN** `textline_boxes` 为空或没有 textline 落在布局区域 bbox 内
- **THEN** 回退到使用原始 `block.bbox`（兼容当前行为）

#### Scenario: textline 大量超出布局 bbox

- **WHEN** 匹配到的 textline 中，有超过 30% 的 bbox 超出原始布局 bbox 范围（可能表明跨区域匹配误差）
- **THEN** 对超过的部分进行截断或回退到原始 bbox，防止 bbox 过度扩展

### Requirement: 表格单元格使用 textline bbox 计算精确边界框

系统在解析表格后，SHALL 使用 `textline_boxes` 为每个单元格计算精确边界框。

#### Scenario: 表格区域内有 textline 数据

- **WHEN** 表格区域 bbox 内有 `textline_boxes` 数据
- **AND** 可以按行列划分近似单元格区域
- **THEN** 系统为每个单元格找到匹配的 textline，计算并集 bbox

#### Scenario: 单元格内没有匹配的 textline

- **WHEN** 某个单元格区域内找不到 textline
- **THEN** 使用按行列比例划分的近似 bbox

## MODIFIED Requirements

### Requirement: paddle_extractor.py 文本块 tight bbox 计算

修改文本块处理逻辑（第603行附近），提取 textline 后在 `_build_text_from_textlines` 之后增加 tight bbox 计算：

```python
# 现有代码
textline_text = PaddleOcrExtractor._build_text_from_textlines(...)

# 新增：从 textline 计算 tight bbox
tight_bbox = self._compute_tight_bbox(
    (float(x1), float(y1), float(x2), float(y2)),
    textline_boxes, textline_texts
)
if tight_bbox:
    pixel_bbox = tight_bbox  # 使用精确 bbox
```

新增 `_compute_tight_bbox` 方法：
```python
@staticmethod
def _compute_tight_bbox(layout_bbox, textline_boxes, textline_texts):
    """从 textline bbox 计算精确的文字边界框
    
    Args:
        layout_bbox: PP-StructureV3 布局区域 bbox (x1,y1,x2,y2)
        textline_boxes: textline bbox 列表
        textline_texts: textline 文本列表
    
    Returns:
        tuple | None: (x1,y1,x2,y2) 精确边界框，或 None
    """
    if not textline_boxes or not textline_texts:
        return None
    
    lx1, ly1, lx2, ly2 = layout_bbox
    matched = []
    for i, tl_box in enumerate(textline_boxes):
        if len(tl_box) < 4:
            continue
        bx, by, bx2, by2 = float(tl_box[0]), float(tl_box[1]), float(tl_box[2]), float(tl_box[3])
        cx, cy = (bx+bx2)/2, (by+by2)/2
        # 检查 textline 中心是否在布局区域内（与 _build_text_from_textlines 一致）
        if lx1 <= cx <= lx2 and ly1 <= cy <= ly2:
            matched.append((bx, by, bx2, by2))
    
    if not matched:
        return None
    
    tight_x1 = min(m[0] for m in matched)
    tight_y1 = min(m[1] for m in matched)
    tight_x2 = max(m[2] for m in matched)
    tight_y2 = max(m[3] for m in matched)
    
    # 防止超出原始布局 bbox 过多（超过 30% 则截断）
    width_ratio = (tight_x2 - tight_x1) / (lx2 - lx1) if (lx2 - lx1) > 0 else 1
    if width_ratio > 1.3:
        tight_x2 = lx2  # 截断到原始布局边界
    
    return (tight_x1, tight_y1, tight_x2, tight_y2)
```

### Requirement: paddle_extractor.py 表格单元格 tight bbox 计算

在表格处理部分（第570行附近），解析 HTML 表格后，为每个单元格计算精确 bbox：

将 table bbox 和 textline_boxes 传入新的 `_compute_cell_bboxes` 方法。

## REMOVED Requirements

（无移除的需求）
