# Checklist

## 未知标签 fallback 处理

- [ ] `paragraph_title` 标签归类为 title 类型文本块
- [ ] `vision_footnote` 标签归类为普通 text 文本块
- [ ] 其他未知标签归类为 text 并记录 WARNING

## 表格识别启用

- [ ] `OCR_SKIP_TABLE=False` 时 `use_table=True`

## 端到端验证

- [ ] 36页标题 "Oxygen transfer efficiency" 被正确识别
- [ ] 36页表格内容被正确识别
- [ ] 38页版面分析不崩溃
- [ ] 38页公式被正确识别
- [ ] 38页公式下方文字被正确识别和翻译
