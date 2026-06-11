# Checklist

## textline 文本提取

- [x] `overall_ocr_res` 中的 `rec_text` 被正确提取，与 `rec_boxes` 一一对应
- [x] 每个 block 的文本内容优先使用 textline 级别文本拼接结果
- [x] 当 `overall_ocr_res` 不可用或匹配不到 textline 时，使用 `block.content` 作为 fallback

## 空格保留验证

- [ ] 38页文本 "abSalzgehalten>2 g TDS/I" 中单词间保留正确空格
- [ ] 38页文本 "keine weiteren oberflachenaktiven Substanzen" 中单词间保留正确空格
- [ ] 38页文本 "im Wesentlichen Einfluss von Meersalz" 中单词间保留正确空格
