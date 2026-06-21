# 代码审查问题修复 Spec

## Why
代码审查发现了3个HIGH、3个MEDIUM和2个LOW级别的问题，涉及变量遮蔽、正则误匹配、未使用函数等，需要修复以提升代码质量。

## What Changes
- 修复`_parse_html_table`中`row_line_counts`变量遮蔽问题（HIGH #1）
- 修复截断逻辑中`max_attempts`变量名遮蔽问题（HIGH #2）
- 修复截断逻辑计数方式不清晰问题（HIGH #3）
- 修复LaTeX环境正则中`gather*?`等星号匹配错误（MEDIUM #4）
- 提取`_parse_html_table`的迭代优化逻辑为独立方法（MEDIUM #5）
- 标注或移除未使用的`fix_line_break_hyphens`函数（MEDIUM #6）
- 移除LaTeX检测中硬编码的TeX Live版本路径（LOW #7）
- 统一注释语言为中文（LOW #8）

## Impact
- Affected code: `modules/ocr/llm_extractor.py` — 变量遮蔽修复 + 方法提取
- Affected code: `modules/pdf_generator.py` — 变量遮蔽修复 + 正则修复 + 路径优化 + 注释统一
- Affected code: `utils/text_processing.py` — 未使用函数处理

## ADDED Requirements

### Requirement: 消除变量遮蔽
代码中不应存在内层变量遮蔽外层同名变量的情况。

#### Scenario: 截断逻辑变量名不遮蔽
- **WHEN** 截断逻辑需要最大尝试次数变量
- **THEN** 应使用`max_truncation_attempts`而非`max_attempts`，避免遮蔽外层字体缩小的`max_attempts`

#### Scenario: 迭代循环中row_line_counts不遮蔽
- **WHEN** 迭代循环内重新创建`row_line_counts`
- **THEN** 应移除Step 1中无用的`row_line_counts`初始化，或重命名为不同名称

### Requirement: LaTeX环境正则正确匹配星号变体
`_preprocess_latex_for_mathtext`中的环境名称正则应正确匹配带星号的环境名。

#### Scenario: gather*环境被正确匹配
- **WHEN** LaTeX文本包含`\begin{gather*}...\end{gather*}`
- **THEN** 正则应匹配`gather*`（星号是环境名的一部分），而非`gathe`或`gather`

### Requirement: 未使用函数标注
新增但未调用的工具函数应标注TODO或移除。

#### Scenario: fix_line_break_hyphens标注
- **WHEN** `fix_line_break_hyphens`函数已定义但无调用点
- **THEN** 应添加TODO注释标注其预期用途

## MODIFIED Requirements

### Requirement: _parse_html_table迭代优化逻辑
将迭代优化逻辑提取为独立的`_compute_table_layout`方法，减少主方法长度。

### Requirement: LaTeX检测路径
移除硬编码的TeX Live年份路径，仅保留glob动态检测。

### Requirement: 注释语言统一
`pdf_generator.py`中新增的英文注释统一为中文。
