# Tasks

- [x] Task 1: 修复变量遮蔽问题
  - [x] SubTask 1.1: `llm_extractor.py` 移除Step 1中无用的`row_line_counts = []`
  - [x] SubTask 1.2: `pdf_generator.py` 将截断逻辑中的`max_attempts = 50`重命名为`max_truncation_attempts = 50`
- [x] Task 2: 修复LaTeX环境正则星号匹配
  - [x] SubTask 2.1: 验证后确认`\*?`语义正确，无需修改
- [x] Task 3: 提取`_parse_html_table`迭代优化逻辑为独立方法
  - [x] SubTask 3.1: 将Step 1-6的迭代优化逻辑提取为`_compute_table_layout(matrix, n_rows, n_cols, table_bbox)`静态方法
  - [x] SubTask 3.2: 在`_parse_html_table`中调用新方法获取`col_widths`, `row_heights`
- [x] Task 4: 处理未使用的`fix_line_break_hyphens`函数
  - [x] SubTask 4.1: 在函数docstring中添加TODO注释
- [x] Task 5: 移除LaTeX检测中硬编码的TeX Live版本路径
  - [x] SubTask 5.1: 移除`/usr/local/texlive/2026/`和`/usr/local/texlive/2025/`硬编码路径
- [x] Task 6: 统一注释语言为中文
  - [x] SubTask 6.1: `pdf_generator.py` 第1129-1136行的英文注释改为中文

# Task Dependencies
- Task 3 依赖 Task 1（提取方法时变量遮蔽问题应已修复）
- 其余任务可并行执行
