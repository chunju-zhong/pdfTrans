# 修复 tight bbox 高度过大 Spec

## Why

`_compute_tight_bbox()` 对宽度有 10% 容差限制，但对高度没有任何限制。tight bbox 的高度从第一个 textline 顶部到最后一个 textline 底部，包含了所有行间距，导致多行文本块的 bbox 高度远大于实际文字高度。此外，font_size 估算在非 TEXT_LABELS 路径使用 `bbox_height * 0.75`，对多行块严重高估字体大小，进而导致 `bg_padding` 过大。

## What Changes

- 在 `_compute_tight_bbox()` 中增加高度容差限制，与宽度限制对称
- 修复非 TEXT_LABELS 路径的 font_size 估算，使用 textline 高度而非整个 bbox 高度

## Impact

- Affected code:
  - `modules/ocr/paddle_extractor.py` — `_compute_tight_bbox()` 高度限制（第 467 行后）、font_size 估算（第 824/861/902/991/1027 行）

## ADDED Requirements

### Requirement: tight bbox 高度容差限制

系统 SHALL 在 `_compute_tight_bbox()` 中对高度增加与宽度对称的容差限制。

#### Scenario: tight bbox 高度超出布局区域
- **WHEN** tight bbox 高度超过布局区域高度的 110%
- **THEN** SHALL 将 tight_y2 截断到布局区域的 ly2
- **AND** SHALL 将 tight_y1 截断到布局区域的 ly1（如果 tight_y1 小于 ly1）

#### Scenario: tight bbox 高度在容差范围内
- **WHEN** tight bbox 高度不超过布局区域高度的 110%
- **THEN** SHALL 保持 tight bbox 高度不变

### Requirement: 非 TEXT_LABELS 路径 font_size 估算使用 textline 高度

系统 SHALL 在 formula、figure_caption、supplement 等非 TEXT_LABELS 路径中，使用 textline 平均高度估算 font_size，而非整个 bbox 高度。

#### Scenario: formula/figure_caption 块 font_size 估算
- **WHEN** OCR 提取 formula 或 figure_caption 类型的文本块
- **THEN** font_size 估算 SHALL 优先使用 textline 平均高度 * 0.75
- **AND** 仅在无 textline 数据时回退到 bbox_height * 0.75

#### Scenario: supplement 块 font_size 估算
- **WHEN** OCR 提取未被布局覆盖的补充文本行
- **THEN** font_size 估算 SHALL 使用单个 textline 高度 * 0.75

## MODIFIED Requirements

### Requirement: _compute_tight_bbox 高度限制

原有逻辑：无高度限制

修改为：增加与宽度对称的高度容差检查
```python
# 防止高度超出原始布局 bbox 过多（超过 10% 则截断）
lheight = ly2 - ly1
if lheight > 0:
    theight = tight_y2 - tight_y1
    if theight / lheight > 1.1:
        tight_y1 = max(tight_y1, ly1)
        tight_y2 = min(tight_y2, ly2)
```
