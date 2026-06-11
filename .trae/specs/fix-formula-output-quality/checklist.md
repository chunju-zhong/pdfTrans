# Checklist

## LaTeX 后处理

- [x] `_clean_latex()` 方法存在且正确清洗多余空格
- [x] 路径 A（parsing_res_list formula 标签）调用 `_clean_latex`
- [x] 路径 B（formula_res_list latex 字段）调用 `_clean_latex`
- [x] `\mathrm{}`/`\text{}` 内字母序列空格被正确合并
- [x] 有意空格命令（`\quad`、`~`、`\,`）被保留
- [x] 截断检测逻辑存在并输出警告

## 公式检测分辨率提升

- [x] `use_formula=True` 时 `text_det_limit_side_len` 为 960
- [x] `use_formula=False` 时 `text_det_limit_side_len` 保持分级默认值

## PDF 公式渲染

- [x] `is_formula=True` 的文本块在 PDF 中渲染为图像
- [x] `is_formula=False` 的文本块保持纯文本插入
- [x] 公式渲染失败时降级为纯文本

## Word 公式渲染

- [x] `is_formula=True` 的文本块在 Word 中转换为 OMML 格式
- [x] `is_formula=False` 的文本块保持纯文本插入
- [x] 公式转换失败时降级为纯文本

## Markdown 公式包裹

- [x] `is_formula=True` 的文本块用 `$...$` 包裹
- [x] `is_formula=False` 的文本块保持原样

## 端到端验证

- [x] "S O T R{=}\frac{f_{\mathrm{d}}\cdot\beta_{S t}\cdot" 清洗后空格减少
- [x] 公式在 PDF 中显示为公式图像而非纯文本
- [x] 公式在 Word 中显示为可编辑公式
- [x] 公式在 Markdown 中被 `$...$` 包裹
