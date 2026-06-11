## MergedBlock 公式属性

- [x] MergedBlock 初始化时自动检测 `is_formula`
- [x] `to_dict()` 包含 `is_formula` 字段
- [x] 有公式块的 MergedBlock → `is_formula = True`
- [x] 无公式块的 MergedBlock → `is_formula = False`

## DOCX 公式文本不重复

- [x] 包含公式块的 MergedBlock 中，公式 LaTeX 不在普通文本中重复输出
- [x] 不包含公式块的 MergedBlock 行为不变
- [x] 纯公式 MergedBlock 不输出多余普通文本
- [x] 公式 OMML 渲染仍正常插入
- [x] 移除公式文本后多余空白被清理

## MD 公式正确包裹

- [x] 行内公式（宽度 < 60%）用 `$...$` 包裹
- [x] 独立行公式（宽度 ≥ 60%）用 `$$...$$` 包裹
- [x] 不包含公式的文本块不被包裹

## 整体验证

- [x] 语法检查通过
- [x] 现有测试通过
