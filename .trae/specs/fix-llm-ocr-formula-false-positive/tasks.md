# Tasks

- [x] Task 1: 移除高 LaTeX 密度检测规则
  - [x] SubTask 1.1: 从 `_detect_formula` 中移除 `_is_high_latex_density` 调用
  - [x] SubTask 1.2: 删除 `_is_high_latex_density` 方法

- [x] Task 2: 改进 `_preprocess_latex_for_mathtext` 支持定界符转换
  - [x] SubTask 2.1: 添加 `\(` → `$`、`\)` → `$` 转换
  - [x] SubTask 2.2: 添加 `\[` → `$$`、`\]` → `$$` 转换

- [ ] Task 3: 添加"无英文单词"检测规则替代高密度检测
  - [ ] SubTask 3.1: 在 `_detect_formula` 中添加 `_is_no_english_words` 检测
  - [ ] SubTask 3.2: 实现 `_is_no_english_words` 方法：去除 LaTeX 命令后检查是否无连续3+英文字母
  - [ ] SubTask 3.3: 条件：无英文单词 + 有 LaTeX 命令 + 无 CJK 字符 → 标记为公式

- [ ] Task 4: 更新测试用例
  - [ ] SubTask 4.1: 添加无英文单词纯公式检测测试
  - [ ] SubTask 4.2: 添加混合文本不误判测试
  - [ ] SubTask 4.3: 验证所有测试通过

# Task Dependencies
- Task 4 依赖 Task 3
