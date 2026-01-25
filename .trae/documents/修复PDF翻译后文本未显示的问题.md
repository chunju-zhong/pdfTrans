# 问题分析

通过查看日志和代码，我已经确认了翻译后文本未显示的根本原因：

1. **核心问题**：在 `_draw_translated_text_v2` 方法中，代码错误地将 `translated_blocks`（包含翻译后文本的文本块）与 `translated_content`（包含原始文本的样式信息）进行匹配，尝试从中获取样式。但实际上，`translated_blocks` 中的每个文本块已经自带完整的样式信息，不需要再从其他来源获取。

2. **样式信息重复**：在 `translation_service.py` 中，生成 `translated_text_block` 时，已经通过 `update_style` 方法将原始文本块的样式信息复制到了翻译后的文本块中。因此，`translated_blocks` 中的文本块已经包含了完整的样式信息。

3. **`insert_textbox` 返回值异常**：由于样式匹配逻辑错误，导致 `insert_textbox` 方法调用时使用了错误的参数，返回了小数（如0.1267378663644223），这是异常的，因为该方法应该返回插入的字符数（整数）。

4. **代码冗余和复杂性**：当前的 `_draw_translated_text_v2` 方法过于复杂，包含了不必要的样式匹配逻辑和过多的字体回退尝试，增加了出错的可能性。

# 解决方案

1. **修复核心逻辑**：移除从 `translated_content` 中获取样式的冗余逻辑，直接使用 `translated_blocks` 中文本块自带的样式信息。

2. **简化绘制流程**：简化 `_draw_translated_text_v2` 方法，减少不必要的复杂性，提高代码的可读性和可靠性。

3. **确保正确调用 `insert_textbox`**：确保 `insert_textbox` 方法使用正确的参数调用，直接使用文本块自带的样式信息。

4. **优化错误处理**：增强错误处理，确保在各种情况下都能生成PDF，即使某些文本块绘制失败。

# 具体修改点

1. **修改 `modules/pdf_generator.py` 文件**：
   - 简化 `_draw_translated_text_v2` 方法，移除从 `translated_content` 中获取样式的逻辑
   - 直接使用 `full_block` 中的样式信息（font, font_size, color等）
   - 移除不必要的字体回退逻辑，只保留基本的字体处理
   - 确保 `insert_textbox` 方法使用正确的参数调用
   - 增强错误处理，确保PDF生成过程更加稳定

# 预期效果

修复后，翻译后的文本将正确显示在生成的PDF中，日志将显示正常的字符插入数量，PDF生成过程更加稳定可靠。