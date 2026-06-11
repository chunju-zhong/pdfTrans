# Checklist

## header 标签标题翻译

- [x] `header` 从 `NON_BODY_LABELS` 中移除
- [x] 36页标题 "Oxygen transfer efficiency" 参与翻译（`is_body_text=True`）
- [x] 真正的重复页眉仍通过 `text_analyzer.py` 的页眉检测逻辑标记为非正文

## 公式背景覆盖

- [x] 公式渲染成功时，在 `insert_image` 之前先绘制白色背景矩形
- [x] 38页公式区域的原文被白色背景覆盖，不与公式图片重叠

## 端到端验证

- [ ] 36页标题 "Oxygen transfer efficiency" 被翻译为中文
- [ ] 38页公式正确渲染且原文背景被覆盖
