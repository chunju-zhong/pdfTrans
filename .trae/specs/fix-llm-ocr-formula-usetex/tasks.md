# Tasks

- [x] Task 1: 修改 `_render_formula_image` 支持 usetex 渲染
  - [x] SubTask 1.1: 添加 `_check_latex_available` 类方法，检测系统 LaTeX 可用性并缓存
  - [x] SubTask 1.2: 修改 `_render_formula_image`，优先使用 `usetex=True` 渲染
  - [x] SubTask 1.3: 添加 `_preprocess_latex_for_mathtext` 方法，去除 mathtext 不支持的命令
  - [x] SubTask 1.4: 实现 usetex → 预处理+mathtext → 纯文本的三级降级策略

- [x] Task 2: 放宽 `_detect_formula` 检测规则
  - [x] SubTask 2.1: 去除首尾空白后再检测定界符（已有 strip，确认生效）
  - [x] SubTask 2.2: 添加"高 LaTeX 密度"检测：LaTeX 命令占比 > 30% 且无 CJK 字符时标记为公式

- [x] Task 3: 更新测试用例
  - [x] SubTask 3.1: 添加 usetex 渲染测试
  - [x] SubTask 3.2: 添加 LaTeX 预处理测试
  - [x] SubTask 3.3: 添加高 LaTeX 密度检测测试
  - [x] SubTask 3.4: 添加 LaTeX 环境检测测试

# Task Dependencies
- Task 3 依赖 Task 1, Task 2
