# Tasks

- [x] Task 1: 修改 `_parse_ref_tags_response()` 解析完整 DeepSeek-OCR 格式
- [x] Task 2: 更新测试使用正则匹配完整块：`<|ref|>(type)<|/ref|><|det|>[[bbox]]<|/det|>\n(actual_text)`
  - [ ] 从 `<|ref|>` 提取类型标签
  - [ ] 从 `<|det|>` 提取 bbox 坐标
  - [ ] 提取 `<|det|>` 后的实际文本内容
  - [ ] 根据类型标签设置 `is_body_text`（title/sub_title → False, text → True）
  - [ ] image 类型创建 PdfImage 而非 TextBlock

- [ ] Task 2: 更新测试
  - [ ] 添加完整 DeepSeek-OCR 格式的解析测试
  - [ ] 添加类型标签映射测试
  - [ ] 添加 image 类型处理测试
  - [ ] 运行全部测试验证无回归

# Task Dependencies
- Task 2 depends on Task 1
