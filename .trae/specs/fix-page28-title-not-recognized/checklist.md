# Checklist

## 核心修复：rec_text 字段名拼写错误

- [x] `rec_text`（单数）改为 `rec_texts`（复数），与 PaddleX `OCRResult` 实际字段名一致
- [x] 修复后 `textline_texts` 不再为空，`_build_text_from_textlines` 可正确匹配文本

## header 标签不再在 OCR 层标记为非正文

- [x] `NON_BODY_LABELS` 不包含 `header`
- [x] `header` 标签的文本块 `is_body_text=True`（默认值）
- [x] 真正的页眉仍由 `text_analyzer.py` 基于多页重复模式识别

## _add_similar_blocks 短文本误判修复

- [x] 短文本（<20字符）仅当完全相同时才标记为非正文
- [x] 长短文本之间使用≥95%的相似度阈值
- [x] 长文本（≥20字符）之间保持≥90%的相似度阈值

## 诊断日志

- [x] OCR 提取日志中包含每个文本块的 `label` 和 `is_body_text` 状态
- [x] rec_texts 长度不匹配时记录 WARNING 日志
- [x] 文本提取失败时记录 `[TEXT_SKIP]` WARNING 日志

## 补充捕获增强

- [x] 补充捕获前提条件从 `len(textline_texts) > 0` 放宽为 `len(textline_boxes) > 0`
- [x] `processed_bboxes` 只收集成功创建 TextBlock 的像素 bbox（`processed_pixel_bboxes`）
- [x] `processed_pixel_bboxes` 在 TEXT_LABELS、figure_caption、else 三个分支正确记录
- [x] `has_textline_texts` 变量安全处理 `textline_texts` 为空的情况

## 端到端验证

- [ ] 第28页段落标题和英文文本被正确识别并翻译
- [ ] 真正的页眉页脚（如重复出现的公司名）仍被正确识别为非正文
