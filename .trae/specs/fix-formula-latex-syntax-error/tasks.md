# Tasks

- [ ] Task 1: 增强 `_clean_latex()` 方法，添加 LaTeX 语法修复能力
  - [ ] SubTask 1.1: 实现花括号匹配修复逻辑（统计 `{`/`}` 数量，移除多余 `}`，补充缺少的 `}`）
  - [ ] SubTask 1.2: 实现常见 OCR 误识别模式纠错（`\{it` → `\mathit`、`,mathrm` → `\mathrm`、`\\ mathtt\\` → `\mathtt`、`{\\ }` 清理）
  - [ ] SubTask 1.3: 修改 `_clean_latex()` 返回值为 `(cleaned_latex, confidence)` 元组，confidence 为 'high'/'medium'/'low'
  - [ ] SubTask 1.4: 更新所有调用 `_clean_latex()` 的地方适配新返回值（paddle_extractor.py 中的两处调用）
  - [ ] SubTask 1.5: 为修复逻辑编写单元测试，覆盖花括号修复和命令纠错场景

- [ ] Task 2: PDF 生成器公式渲染重试机制
  - [ ] SubTask 2.1: 在 `pdf_generator.py` 的公式渲染逻辑中，首次渲染失败后调用修复版 `_clean_latex()` 重试
  - [ ] SubTask 2.2: 重试仍失败时，降级为纯文本并标记公式质量低
  - [ ] SubTask 2.3: 编写测试验证重试机制

- [ ] Task 3: DOCX 生成器公式转换重试机制
  - [ ] SubTask 3.1: 在 `docx_generator.py` 的 `_insert_formula_omml()` 中，首次转换失败后调用修复版 `_clean_latex()` 重试
  - [ ] SubTask 3.2: 重试仍失败时，降级为纯文本
  - [ ] SubTask 3.3: 编写测试验证重试机制

- [ ] Task 4: Markdown 生成器公式语法验证
  - [ ] SubTask 4.1: 在 `markdown_generator.py` 的公式输出逻辑中，添加花括号匹配验证
  - [ ] SubTask 4.2: 验证失败时尝试修复，无法修复时添加 `<!-- formula-quality:low -->` 标记
  - [ ] SubTask 4.3: 编写测试验证

- [ ] Task 5: 端到端验证
  - [ ] SubTask 5.1: 使用 38-39 页 PDF 重新运行翻译，验证 PDF 中公式渲染为图像而非纯文本
  - [ ] SubTask 5.2: 验证 Word 中公式以 OMML 格式正确显示
  - [ ] SubTask 5.3: 验证 Markdown 中公式用 `$$...$$` 包裹且 LaTeX 语法正确

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 2, Task 3, Task 4]
