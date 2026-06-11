# Checklist

## MathML 到 OMML 树形转换

- [x] `_mathml_to_omml` 使用 lxml 树形解析，而非字符串替换
- [x] `<msub>` 正确转换为 `<m:sSub><m:e>base</m:e><m:sub>subscript</m:sub></m:sSub>`
- [x] `<msup>` 正确转换为 `<m:sSup><m:e>base</m:e><m:sup>superscript</m:sup></m:sSup>`
- [x] `<msubsup>` 正确转换为 `<m:sSubSup><m:e>base</m:e><m:sub>sub</m:sub><m:sup>sup</m:sup></m:sSubSup>`
- [x] `<mfrac>` 正确转换为 `<m:f><m:fPr>...</m:fPr><m:num>...</m:num><m:den>...</m:den></m:f>`
- [x] `<mi>`/`<mo>`/`<mn>` 正确转换为 `<m:r><m:t>text</m:t></m:r>`
- [x] `<mrow>`/`<mstyle>` 等容器元素递归处理子元素
- [x] 未识别的 MathML 元素递归处理子元素作为 fallback

## Word 输出验证

- [ ] 38页公式在 Word 中正确显示为 OMML 公式对象
- [ ] 不再出现 `Opening and ending tag mismatch` 错误
- [ ] 公式不再降级为 LaTeX 文本
