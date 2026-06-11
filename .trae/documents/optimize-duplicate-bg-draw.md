# 优化 pdf_generator.py 中重复的背景绘制逻辑

## 问题分析

在 [pdf_generator.py:242-267](file:///Users/chunju/work/pdfTrans/modules/pdf_generator.py#L242-L267) 中，绘制白色背景矩形的逻辑重复了两次：

1. **第 245-252 行**：公式分支内，在渲染公式图片之前画白色背景覆盖原文
2. **第 258-265 行**：公式分支外（普通文本），画白色背景覆盖原文

两段代码完全相同：
```python
bg_padding = original_font_size
bg_rect = fitz.Rect(
    rect.x0,
    max(rect.y0 - bg_padding, 0),
    rect.x1,
    min(rect.y1 + bg_padding, page.rect.height)
)
page.draw_rect(bg_rect, color=(1, 1, 1), fill=True, width=0)
```

## 优化方案

将背景绘制逻辑提取到公式分支判断**之前**，只保留一份。无论走公式路径还是文本路径，都需要先画白色背景覆盖原文。

### 具体步骤

1. 将 `bg_padding` / `bg_rect` / `page.draw_rect(...)` 三行移到 `if getattr(full_block, 'is_formula', False)` 判断之前（即第 242 行之前）
2. 在公式分支内删除重复的背景绘制代码（第 245-252 行）
3. 在公式分支外删除重复的背景绘制代码（第 258-265 行），保留 debug 日志行
4. 将 debug 日志移到统一位置（背景绘制之后）

### 优化后代码结构

```python
# 创建文本框
rect = fitz.Rect(block_bbox[0], block_bbox[1], block_bbox[2], block_bbox[3])
logger.debug(f"文本框尺寸: {rect.width}x{rect.height}")

# 统一绘制白色背景覆盖原文
bg_padding = original_font_size
bg_rect = fitz.Rect(
    rect.x0,
    max(rect.y0 - bg_padding, 0),
    rect.x1,
    min(rect.y1 + bg_padding, page.rect.height)
)
page.draw_rect(bg_rect, color=(1, 1, 1), fill=True, width=0)
logger.debug(f"绘制背景色覆盖原文，区域: {bg_rect} (padding={bg_padding:.1f})")

if getattr(full_block, 'is_formula', False) and full_block.block_text:
    try:
        img_buf = self._render_formula_image(full_block.block_text, fontsize=original_font_size)
        page.insert_image(rect, stream=img_buf.getvalue())
        continue
    except Exception as e:
        logger.warning(f'公式渲染失败，降级为文本: {e}')

# 使用默认左对齐
alignment = 0
...
```

### 影响范围

- 仅修改 `pdf_generator.py` 第 242-267 行区域
- 不改变任何业务逻辑，只是消除代码重复
- 公式渲染失败降级为文本时，背景已提前绘制好，行为不变
