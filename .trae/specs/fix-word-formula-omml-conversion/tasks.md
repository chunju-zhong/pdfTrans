# Tasks

- [x] Task 1: 重写 `_mathml_to_omml` 方法，使用 lxml 树形解析替代字符串替换
  - [x] SubTask 1.1: 实现 `_mathml_to_omml_element` 递归方法，将 MathML 元素树转换为 OMML 元素树
  - [x] SubTask 1.2: 正确处理 `<msub>`/`<msup>`/`<msubsup>` 的 base/sub/sup 子元素边界
  - [x] SubTask 1.3: 正确处理 `<mfrac>` 的 numerator/denominator 子元素边界
  - [x] SubTask 1.4: 处理 `<mi>`/`<mo>`/`<mn>` 为 `<m:r><m:t>` 文本运行
  - [x] SubTask 1.5: 处理 `<mrow>`/`<mstyle>` 等容器元素（递归处理子元素）
  - [x] SubTask 1.6: 对未识别的 MathML 元素，递归处理子元素作为 fallback
- [x] Task 2: 修改 `_insert_formula_omml` 方法，使用新的树形转换
  - [x] SubTask 2.1: 调用新的 `_mathml_to_omml_element` 方法，将返回的 OMML 元素直接 append 到 paragraph

# Task Dependencies

- [Task 2] depends on [Task 1]
