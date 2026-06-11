# 修复标题文本包含换行符导致截断 Spec

## Why

从日志第47-68行可以看到，标题 "2.3 EXECUTION OF GROUND INVESTIGATION" 翻译后显示为 "2.3..."，文本被过度截断。根因是翻译文本包含换行符 `"2.3\n地质勘察的实施"`，被分成两行，但文本框高度只有13.3pt（单行高度），无法容纳多行文本。

## 根因分析

### 文本框尺寸分析

从日志第47行：
- 文本框：`Rect(72.0, 241.97, 358.63, 255.25)`
- 宽度：286.6pt（足够容纳单行文本）
- 高度：13.3pt（仅1行高度）
- 字体大小：12.0pt
- 翻译文本："2.3\n地质勘察的实施"（11字符，包含换行符）

### 关键发现

从日志第48-49行：
```
溢出文本: '2.3
地质勘察的实施...' (完整长度=11)
```

文本被分成两行：
- 第一行："2.3"
- 第二行："地质勘察的实施"

### 问题链

1. **原文可能是分行的** → 标题号和标题内容在不同行或不同文本块
2. **翻译保留了换行符** → 翻译API或文本处理保留了原文的换行符结构
3. **文本框高度不足** → 文本框高度13.3pt只能容纳1行，但文本需要2行
4. **触发截断逻辑** → 最终截断到40%，只剩 "2.3..."

### 与宽度问题的关系

**宽度足够**：286.6pt可以容纳单行文本（11个中文字符约132pt）
**但换行符导致多行**：文本被分成2行，需要更多高度

## What Changes

- **处理翻译文本中的换行符**：在渲染前检查文本是否包含换行符，如果包含则计算需要的行数并扩展文本框高度
- **增加换行符检测**：在文本渲染前检测换行符，根据行数计算所需高度
- **扩展文本框高度**：如果文本包含换行符，扩展文本框高度以容纳所有行

## Impact

- Affected code: `modules/pdf_generator.py` 的 `_draw_translated_text` 方法
- 行为变更：文本包含换行符时会扩展文本框高度，而非直接截断
- 影响范围：所有翻译 PDF 生成，特别是标题和短文本块

## ADDED Requirements

### Requirement: 处理翻译文本中的换行符

系统 SHALL 在渲染翻译文本前检测是否包含换行符，如果包含则根据行数扩展文本框高度。

#### Scenario: 文本包含换行符

- **WHEN** 翻译文本包含换行符（`\n`）
- **THEN** 系统计算需要的行数：`行数 = 文本.split('\n').length`
- **AND** 计算所需高度：`所需高度 = 行数 * 字体大小 * 行高倍率`
- **AND** 如果所需高度 > 文本框高度，扩展文本框高度

#### Scenario: 文本框高度扩展

- **WHEN** 文本包含换行符且需要更多高度
- **THEN** 扩展文本框高度到所需高度（上限为页面底部或下一文本块顶部）
- **AND** 记录扩展日志：原始高度、扩展后高度、行数

#### Scenario: 文本不包含换行符

- **WHEN** 翻译文本不包含换行符
- **THEN** 保持原有逻辑，不扩展文本框高度

## MODIFIED Requirements

### Requirement: 文本渲染前检测换行符

修改 `pdf_generator.py` 的 `_draw_translated_text` 方法，在文本渲染前增加换行符检测和文本框高度扩展逻辑：

修改前：
```python
# 直接使用原始bbox
rect = fitz.Rect(block_bbox[0], block_bbox[1], block_bbox[2], block_bbox[3])
```

修改后：
```python
# 检测换行符并扩展文本框高度
if '\n' in translated_text:
    lines = translated_text.split('\n')
    required_height = len(lines) * original_font_size * original_lineheight
    if required_height > rect.height:
        # 扩展文本框高度
        new_y1 = min(rect.y0 + required_height, page.rect.height)
        rect = fitz.Rect(rect.x0, rect.y0, rect.x1, new_y1)
        logger.info(f"[换行符处理] 文本包含{len(lines)}行，扩展文本框高度: {rect.height:.1f} -> {new_y1 - rect.y0:.1f}")
```

## REMOVED Requirements

（无移除的需求）