# Tasks

- [x] Task 1: 添加 LaTeX 后处理函数
  - [x] SubTask 1.1: 在 `paddle_extractor.py` 中添加 `_clean_latex(latex)` 静态方法，实现：去除多余空格、合并连续空格、修复 `\mathrm{}`/`\text{}` 内字母序列空格、去除 `{}` 前后多余空格、截断检测
  - [x] SubTask 1.2: 在路径 A（parsing_res_list 的 formula 标签）调用 `_clean_latex`
  - [x] SubTask 1.3: 在路径 B（formula_res_list 的 latex 字段）调用 `_clean_latex`

- [x] Task 2: 公式检测分辨率提升
  - [x] SubTask 2.1: 修改 `_create_pipeline()`，当 `use_formula=True` 时，将 `text_det_limit_side_len` 强制设为 960

- [x] Task 3: PDF 公式渲染
  - [x] SubTask 3.1: 在 `pdf_generator.py` 中添加 `_render_formula_image(latex, fontsize)` 方法，使用 matplotlib 将 LaTeX 渲染为 PNG 图像
  - [x] SubTask 3.2: 修改 `_draw_translated_text()`，检测 `is_formula=True` 时调用公式渲染方法，将图像嵌入到 bbox 位置
  - [x] SubTask 3.3: 处理公式渲染失败时的降级逻辑（回退到纯文本）

- [x] Task 4: Word 公式渲染
  - [x] SubTask 4.1: 在 `docx_generator.py` 中添加 LaTeX → OMML 转换方法（使用 latex2mathml + mathml2omml 或类似库）
  - [x] SubTask 4.2: 修改 `_add_merged_text()`，检测 `is_formula=True` 时插入 OMML 公式
  - [x] SubTask 4.3: 处理公式转换失败时的降级逻辑（回退到纯文本）

- [x] Task 5: Markdown 公式包裹
  - [x] SubTask 5.1: 修改 `markdown_generator.py`，检测 `is_formula=True` 时用 `$...$` 包裹公式文本

# Task Dependencies

- [Task 1] 独立，必须首先完成（其他任务依赖清洗后的 LaTeX）
- [Task 2] 独立
- [Task 3] 依赖 [Task 1]
- [Task 4] 依赖 [Task 1]
- [Task 5] 独立
