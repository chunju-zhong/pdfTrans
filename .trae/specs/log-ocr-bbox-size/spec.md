# 打印 LLM OCR 识别到的文本框大小 Spec

## Why

排查藏文 OCR bbox 宽度问题时，需要直观看到每个识别到的文本框的具体尺寸（PDF 点坐标下的宽度和高度），以便评估 LLM 返回的 bbox 是否覆盖了完整的文本行。当前代码没有在 `_create_text_block` 中输出 bbox 尺寸信息，只能在日志中看到汇总的行数统计。

## What Changes

- 在 `_create_text_block` 中增加 INFO 级别日志，输出每个文本块的 bbox 坐标和宽高

## Impact

- Affected code:
  - `modules/ocr/llm_extractor.py` — `_create_text_block` 方法

## ADDED Requirements

### Requirement: `_create_text_block` 输出 bbox 尺寸日志

`_create_text_block` SHALL 在创建 TextBlock 后，以 INFO 级别日志输出每个文本块的页码、bbox 坐标、宽度(pt)、高度(pt) 和文本内容（前 50 字符）。

#### Scenario: 第 6 页藏文 OCR 处理

- **WHEN** `_create_text_block` 处理第 6 页的一个 OcrBlock
- **THEN** 日志输出类似：
  ```
  第6页 text_block#0 bbox=(42.2, 20.4, 296.1, 46.8) 宽=253.9pt 高=26.4pt 文本="..."
  ```

#### Scenario: 非藏文页面

- **WHEN** 处理英文等其他语言的页面
- **THEN** 同样输出 bbox 尺寸日志，便于对比排查
