# Tasks - 添加CLI命令行支持

- [x] Task 1: 创建CLI基础框架
  - [x] SubTask 1.1: 创建 cli.py 主入口文件，使用argparse实现命令解析
  - [x] SubTask 1.2: 创建 cli/__init__.py 初始化文件
  - [x] SubTask 1.3: 实现全局选项解析（--help, --verbose, --version）
  - [x] SubTask 1.4: 实现子命令路由机制（translate, glossary, list-languages）

- [x] Task 2: 实现 translate 命令
  - [x] SubTask 2.1: 创建 cli/translate_command.py 文件
  - [x] SubTask 2.2: 实现命令行参数解析（input, output, source, target, translator, pages, format, glossary, doc-type, semantic-merge, llm-merge, chapter-split）
  - [x] SubTask 2.3: 实现输入文件验证（检查文件存在、格式正确）
  - [x] SubTask 2.4: 调用 translation_service 执行翻译
  - [x] SubTask 2.5: 实现进度显示（在verbose模式下）
  - [x] SubTask 2.6: 实现章节拆分功能支持

- [x] Task 3: 实现 glossary 命令
  - [x] SubTask 3.1: 创建 cli/glossary_command.py 文件
  - [x] SubTask 3.2: 实现命令行参数解析（input, output, source, target, translator, pages, doc-type）
  - [x] SubTask 3.3: 实现输入文件验证
  - [x] SubTask 3.4: 调用 glossary_service 执行术语提取
  - [x] SubTask 3.5: 实现进度显示

- [x] Task 4: 实现 list-languages 命令
  - [x] SubTask 4.1: 创建 cli/list_languages_command.py 文件
  - [x] SubTask 4.2: 从 config.py 读取支持的语言列表
  - [x] SubTask 4.3: 格式化输出语言列表

- [x] Task 5: 创建进度显示组件
  - [x] SubTask 5.1: 创建 cli/progress_display.py 文件
  - [x] SubTask 5.2: 实现控制台进度条显示
  - [x] SubTask 5.3: 实现阶段信息显示
  - [x] SubTask 5.4: 支持 verbose 模式的详细日志输出

- [x] Task 6: 扩展 translation_service 支持同步调用
  - [x] SubTask 6.1: 在 TranslationService 类中添加 process_translation_sync 方法
  - [x] SubTask 6.2: 实现同步进度回调机制
  - [x] SubTask 6.3: 确保同步方法返回完整结果

- [x] Task 7: 扩展 glossary_service 支持同步调用
  - [x] SubTask 7.1: 在 GlossaryService 类中添加 extract_glossary_sync 方法
  - [x] SubTask 7.2: 实现同步进度回调机制
  - [x] SubTask 7.3: 确保同步方法返回完整结果

- [x] Task 8: 配置命令行入口
  - [x] SubTask 8.1: 创建 setup.py 或更新 pyproject.toml
  - [x] SubTask 8.2: 配置 console_scripts 入口点
  - [x] SubTask 8.3: 确保 pdftrans 命令可用

- [x] Task 9: 编写CLI测试
  - [x] SubTask 9.1: 创建 tests/test_cli.py 测试文件
  - [x] SubTask 9.2: 测试命令行参数解析
  - [x] SubTask 9.3: 测试 translate 命令
  - [x] SubTask 9.4: 测试 glossary 命令
  - [x] SubTask 9.5: 测试 list-languages 命令

- [x] Task 10: 更新文档
  - [x] SubTask 10.1: 更新 README.md 添加CLI使用说明
  - [x] SubTask 10.2: 添加CLI示例到文档

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 1
- Task 5 can be done in parallel with Task 2-4
- Task 6 depends on Task 2
- Task 7 depends on Task 3
- Task 8 depends on Task 1-4
- Task 9 depends on Task 1-8
- Task 10 depends on Task 1-9
