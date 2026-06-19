# Tasks

- [x] Task 1: 将 $$...$$ 转换为 $...$（display math → inline math）
  - [x] SubTask 1.1: 在 `_preprocess_latex_for_mathtext` 中添加 `$$...$$` → `$...$` 转换
  - [x] SubTask 1.2: 确保转换顺序正确（先转定界符，再处理命令）

- [x] Task 2: 配置 matplotlib CJK 字体
  - [x] SubTask 2.1: 在 `_render_mixed_text_formula_image` 中设置 CJK 字体
  - [x] SubTask 2.2: 在 `_try_mathtext_render` 中设置 CJK 字体
  - [x] SubTask 2.3: 在 `_render_formula_image` 的 usetex 分支中设置 CJK 字体

- [x] Task 3: 更新测试用例并验证
  - [x] SubTask 3.1: 添加 $$...$$ → $...$ 转换测试
  - [x] SubTask 3.2: 添加 CJK 字体配置测试
  - [x] SubTask 3.3: 验证所有测试通过（78个）

# Task Dependencies
- Task 3 depends on Task 1, Task 2
