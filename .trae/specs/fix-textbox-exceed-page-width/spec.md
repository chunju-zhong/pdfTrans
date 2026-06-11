# 修复文本框超出原文宽度和页宽度 Spec

## Why

第24页第一段话的文本框超出了原文宽度，甚至超出了页面宽度。本次运行未使用语义合并。根因有两个：

1. **PDF 生成器溢出扩展无页面宽度限制**（主因）：当翻译文本溢出原始 bbox 时，`pdf_generator.py` 每次将文本框宽度扩展 10%（最多 3 次，总计可达 33%），但扩展后的右边界不限制在页面宽度内，导致文本框超出页面。
2. **OCR tight bbox 可比布局区域宽最多 30%**（加剧因素）：`paddle_extractor.py` 的 `_compute_tight_bbox()` 使用 textline bbox 的并集计算精确边界，当 textline 检测有噪声时，tight bbox 可比布局区域宽最多 30% 才被截断。这两个问题叠加，使文本框更容易超出页面。

## What Changes

- 修复 `pdf_generator.py` 溢出重试逻辑：扩展文本框时限制右边界不超过页面宽度
- 修复 `paddle_extractor.py` tight bbox 计算：将 30% 容差降低到更合理的值，并增加页面宽度限制

## Impact

- Affected code:
  - `modules/pdf_generator.py` — 溢出重试时文本框扩展逻辑（第 302-314 行）
  - `modules/ocr/paddle_extractor.py` — `_compute_tight_bbox()` 容差和页面宽度限制（第 468-473 行）

## ADDED Requirements

### Requirement: PDF 生成器文本框扩展不超出页面

系统 SHALL 在 PDF 生成器溢出重试时，确保扩展后的文本框右边界不超过页面宽度。

#### Scenario: 溢出重试扩展文本框
- **WHEN** 翻译文本溢出原始文本框
- **AND** PDF 生成器尝试扩展文本框宽度（每次 10%）
- **THEN** 扩展后的文本框右边界 SHALL 不超过页面宽度
- **AND** 文本框下边界 SHALL 不超过页面高度

#### Scenario: 扩展后仍溢出
- **WHEN** 文本框已扩展到页面宽度边界
- **AND** 翻译文本仍然溢出
- **THEN** SHALL 进入缩小字体策略（attempt 4-5），而非继续扩展

### Requirement: OCR tight bbox 不超出布局区域和页面宽度

系统 SHALL 确保 OCR 提取的 tight bbox 不超出布局区域过多，且不超出页面宽度。

#### Scenario: textline bbox 超出布局区域
- **WHEN** OCR 检测的 textline bbox 比布局区域宽
- **THEN** tight bbox 的宽度 SHALL 不超过布局区域宽度的 110%（当前为 130%）
- **AND** tight bbox 的右边界 SHALL 不超出页面宽度

#### Scenario: tight bbox 超出页面宽度
- **WHEN** 计算出的 tight bbox 右边界超出页面宽度
- **THEN** SHALL 将右边界截断到页面宽度

## MODIFIED Requirements

### Requirement: PDF 生成器溢出扩展

原有逻辑（第 302-314 行）：
```python
new_width = current_rect.width * 1.1
current_rect = fitz.Rect(
    current_rect.x0,
    current_rect.y0,
    current_rect.x0 + new_width,   # 无页面宽度限制
    current_rect.y0 + new_height   # 无页面高度限制
)
```

修改为：
```python
new_width = current_rect.width * 1.1
new_height = current_rect.height * 1.2
current_rect = fitz.Rect(
    current_rect.x0,
    current_rect.y0,
    min(current_rect.x0 + new_width, page.rect.width),   # 限制不超过页面宽度
    min(current_rect.y0 + new_height, page.rect.height)   # 限制不超过页面高度
)
```

### Requirement: OCR tight bbox 容差

原有逻辑（第 468-473 行）：
```python
if twidth / lwidth > 1.3:   # 30% 容差
    tight_x2 = lx2
```

修改为：
```python
if twidth / lwidth > 1.1:   # 10% 容差
    tight_x2 = lx2
```

并增加页面宽度限制：
```python
# 确保 tight bbox 不超出页面宽度
page_width = page_info.get('page_width_pts', float('inf'))
if tight_x2 * scale_x > page_width:
    tight_x2 = page_width / scale_x
```
