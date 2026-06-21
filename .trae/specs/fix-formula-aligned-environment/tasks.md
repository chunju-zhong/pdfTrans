# Tasks

- [x] Task 1: 修复 `_check_latex_available()` 的 LaTeX 检测路径
  - [x] SubTask 1.1: 在 PATH 检测失败后，依次探测 macOS 常见 LaTeX 安装路径（`/Library/TeX/texbin/latex`、`/usr/local/texlive/*/bin/universal-darwin/latex`、`/opt/homebrew/bin/latex`）
  - [x] SubTask 1.2: 若在非 PATH 路径找到 LaTeX，将其目录加入 `os.environ['PATH']`
  - [x] SubTask 1.3: 添加日志记录 LaTeX 检测结果和实际使用的路径
  - [x] SubTask 1.4: 验证 usetex 渲染在修复后可用
- [x] Task 2: 在 `_detect_formula()` 中增加 `\begin{...}` 数学环境检测
  - [x] SubTask 2.1: 定义数学环境名称集合（aligned, gathered, cases, equation, equation*, align, align*, gather, gather*, matrix, pmatrix, bmatrix, vmatrix）
  - [x] SubTask 2.2: 检测文本是否以 `\begin{env_name}` 开头且以 `\end{env_name}` 结尾
  - [x] SubTask 2.3: 若匹配，去除环境标记，返回 `(True, 去除环境后的内容)`
  - [x] SubTask 2.4: 添加单元测试验证检测逻辑
- [x] Task 3: 在 `_preprocess_latex_for_mathtext()` 中增加 `\begin{aligned}` 环境转换
  - [x] SubTask 3.1: 在预处理步骤中添加 `\begin{aligned}...\end{aligned}` 检测与转换
  - [x] SubTask 3.2: 去除 `\begin{aligned}` 和 `\end{aligned}` 标记
  - [x] SubTask 3.3: 将 `\\` 分隔的多行内容用空格连接为单行
  - [x] SubTask 3.4: 去除每行行首的 `&` 对齐标记
  - [x] SubTask 3.5: 对 `\begin{gathered}`、`\begin{cases}` 做类似处理
  - [x] SubTask 3.6: 添加单元测试验证转换逻辑
- [x] Task 4: usetex 模式加载 amsmath 宏包
  - [x] SubTask 4.1: 在 `_render_formula_image` 的 usetex 路径中添加 `\usepackage{amsmath}` preamble
  - [x] SubTask 4.2: 在 `_render_mixed_text_formula_image` 的 usetex 路径中添加同样的 preamble
  - [x] SubTask 4.3: 验证 `\begin{aligned}` 公式在 usetex 模式下正确渲染

# Task Dependencies
- Task 2 和 Task 3 互相独立，可并行执行
- Task 1 是最高优先级（修复后 usetex 可直接渲染 `\begin{aligned}`，无需 mathtext 降级）
- Task 4 依赖 Task 1（需要 LaTeX 被正确检测后 usetex 才可用）
