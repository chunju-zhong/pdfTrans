# Tasks

- [x] Task 1: 修复 LaTeX 环境正则使用反向引用确保 begin/end 环境名一致
  - [x] SubTask 1.1: 将 `_preprocess_latex_for_mathtext` 中 `env_names` 正则改为捕获组 + 反向引用：`r'\\begin\{(aligned|gathered|cases|equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}'`
  - [x] SubTask 1.2: 修改 lambda 中 `m.group(1)` 为 `m.group(2)`（group(1) 现在是环境名）
  - [x] SubTask 1.3: 编写测试验证不同环境名不匹配、相同环境名正确去除

- [x] Task 2: 修复兜底 `\\` 和 `&` 替换过于激进的问题
  - [x] SubTask 2.1: 将兜底 `re.sub(r'\\\\', ' ', latex)` 改为仅在检测到残留 `\\` 行分隔符模式时执行（如 `\\` 后跟换行或行尾）
  - [x] SubTask 2.2: 将兜底 `latex.replace('&', '')` 改为仅在检测到残留 `&` 对齐标记模式时执行（如 `&` 前后为非 `&` 字符的对齐模式）
  - [x] SubTask 2.3: 验证幂等性（对已处理结果再次调用不改变输出）

- [x] Task 3: 修复 `_check_latex_available` 的线程安全问题
  - [x] SubTask 3.1: 将 PATH 检测和 `os.environ['PATH']` 修改移入 `_latex_lock` 保护范围内

- [x] Task 4: 移除 `llm_extractor.py` 中未使用的 `fix_line_break_hyphens` import
  - [x] SubTask 4.1: 删除 `from utils.text_processing import fix_line_break_hyphens` 行

- [x] Task 5: 在 `_compute_table_layout` 的 docstring 中标注副作用
  - [x] SubTask 5.1: 在 docstring 中添加说明：此方法会修改传入 `matrix` 参数中单元格的 `estimated_lines` 属性

- [x] Task 6: 修复 `_parse_html_table` 返回值检查不一致
  - [x] SubTask 6.1: 在 `_map_ocr_blocks_to_models` 中将 `if cells:` 改为 `if cells is not None:`

- [x] Task 7: 扩展 `_estimate_text_display_width` 的 CJK 宽度估算范围
  - [x] SubTask 7.1: 在 CJK 判断条件中增加日文平假名（\u3040-\u309F）、片假名（\u30A0-\u30FF）、韩文（\uAC00-\uD7AF）

- [x] Task 8: 优化表格单元格截断为二分查找
  - [x] SubTask 8.1: 将 CJK 逐字符截断和英文逐词截断改为二分查找，减少 `insert_textbox` 调用次数

- [x] Task 9: 收窄 `docx_generator.py` 合并单元格异常捕获范围
  - [x] SubTask 9.1: 将 `except Exception as e:` 改为 `except (ValueError, KeyError) as e:`

- [x] Task 10: 修复 `llm_extractor.py` 模块级 import 顺序
  - [x] SubTask 10.1: 将 `import base64` 和 `import logging` 移到文件顶部与其他 import 一起，常量 `TABLE_HTML_MARKER` 移到 import 之后

- [x] Task 11: 扩展 `_check_latex_available` 的 LaTeX 路径探测支持 Linux 和 Windows
  - [x] SubTask 11.1: 在 `common_paths` 列表中添加 Linux 常见路径：`/usr/bin/latex`、`/usr/local/texlive/*/bin/x86_64-linux/latex`、`/usr/local/texlive/*/bin/aarch64-linux/latex`
  - [x] SubTask 11.2: 添加 Windows 常见路径：`C:/texlive/*/bin/windows/latex.exe`、`C:/Program Files/MiKTeX/miktex/bin/x64/latex.exe`
  - [x] SubTask 11.3: 使用 `sys.platform` 或 `platform.system()` 条件化路径探测，避免在非目标平台执行无意义的 glob

# Task Dependencies
- Task 1 和 Task 2 相关（同一函数），建议顺序执行
- Task 3 和 Task 11 相关（同一函数），建议顺序执行
- Task 4, 5, 6, 7, 9, 10 独立，可并行
- Task 8 独立
