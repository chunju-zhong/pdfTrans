# Tasks

- [x] Task 1: 增强 `_preprocess_latex_for_mathtext` 处理更多不支持的命令
  - [x] SubTask 1.1: 添加希腊字母替换（\alpha → α, \beta → β 等，共48个）
  - [x] SubTask 1.2: 添加数学符号替换（\circ → °, \cdot → ·, \% → % 等，共20个）
  - [x] SubTask 1.3: 处理 `\(...\)` 和 `\[...\]` 定界符转换为 `$...$` 和 `$$...$$`
  - [x] SubTask 1.4: 去除 `\left` 和 `\right` 命令

- [x] Task 2: 修改公式渲染失败降级策略
  - [x] SubTask 2.1: `is_formula=True` 渲染失败时，先用预处理后的 LaTeX 重新渲染，而非直接降级为纯文本
  - [x] SubTask 2.2: 添加 `_try_mathtext_render` 辅助方法，封装 mathtext 渲染逻辑
  - [x] SubTask 2.3: 三级降级：原始 mathtext → 预处理+mathtext → 返回 None
  - [x] SubTask 2.4: 处理 `_render_formula_image` 返回 None 的情况

- [x] Task 3: 添加混合公式文本的公式片段提取渲染
  - [x] SubTask 3.1: 添加 `_contains_latex_formula` 静态方法，检测 $...$、$$...$$、\(...\)、\[...\]
  - [x] SubTask 3.2: 添加 `_render_mixed_text_formula_image` 方法，将混合文本整体渲染为图片
  - [x] SubTask 3.3: 在 PDF 生成器中，对非公式文本块检测 LaTeX 片段并渲染

- [x] Task 4: 更新测试用例
  - [x] SubTask 4.1: 测试预处理增强（希腊字母、数学符号、\left\right）
  - [x] SubTask 4.2: 测试公式渲染失败降级策略
  - [x] SubTask 4.3: 测试混合公式文本的片段检测和渲染

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 1, Task 2, Task 3
