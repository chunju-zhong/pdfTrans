# 更新日志

## 2026-03-16

- 实现翻译进度系统重构：
  - 创建 `models/phase_config.py` 文件，定义翻译各阶段配置，包括提取、翻译、合并、生成和清理阶段
  - 修改 `models/task.py`，添加 `CopyableMixin` 继承，实现深拷贝支持
  - 添加任务类型设置方法 `set_task_type()`，支持翻译和术语提取两种任务类型
  - 添加阶段进度更新方法 `update_phase_progress()`，支持细粒度进度跟踪
  - 添加任务开始和结束时间记录功能
  - 将 `threading.Lock()` 升级为 `threading.RLock()`，支持递归锁
- 优化翻译服务进度更新：
  - 修改 `services/translation_service.py`，使用 `update_phase_progress()` 替代 `update_progress()`
  - 实现各阶段的细粒度进度更新（提取、翻译、合并、生成、清理）
  - 添加拷贝页面的进度更新功能
  - 优化页面处理的进度计算
- 实现语义块两阶段合并功能：
  - 创建 `utils/text_processing.py` 中的 `merge_semantic_blocks_with_llm_two_phase()` 函数
  - 第一阶段：基于句子级别判断进行语义合并
  - 第二阶段：基于段落级别判断进行语义合并
  - 添加 `_check_paragraph_continuation()` 函数，判断段落是否延续
  - 优化翻译服务的合并逻辑调用
- 优化文本块合并算法：
  - 修改 `utils/text_processing.py` 中的 `merge_semantic_blocks()` 函数
  - 改进句子延续判断，支持更多标点类型开头（小写字母、标点符号）
  - 添加段落延续判断，确保同一段落的文本块正确合并
  - 优化垂直距离检查和章节信息处理
- 添加新的数据模型：
  - 创建 `models/copyable.py`，实现 `CopyableMixin` 抽象类，支持深拷贝
  - 创建 `models/phase_config.py`，定义翻译阶段配置常量
- 优化术语表提取服务：
  - 修改 `services/glossary_service.py`，支持术语提取的进度跟踪
  - 优化术语提取逻辑，提高提取准确性
- 修复测试用例：
  - 更新 `tests/test_semantic_analyzer.py`，修复合并块数量断言
  - 更新 `tests/test_title_body_separation.py`，修复标题与正文分离测试断言
  - 更新 `tests/test_pdf_page_translation.py`，修复mock验证问题
- 创建新测试用例：
  - 创建 `tests/test_two_phase_merge.py`，测试两阶段合并功能
  - 创建 `tests/test_split_sentence.py`，测试句子拆分功能
  - 创建 `tests/test_list_detection.py`，测试列表检测功能
- 相关文件：
  - `models/task.py`
  - `models/phase_config.py`
  - `models/copyable.py`
  - `services/translation_service.py`
  - `services/glossary_service.py`
  - `utils/text_processing.py`
  - `modules/markdown_generator.py`
  - `modules/semantic_analyzer.py`
  - `tests/test_two_phase_merge.py`
  - `tests/test_split_sentence.py`
  - `tests/test_list_detection.py`

## 2026-03-13

- 修复PDF章节标题位置识别问题：
  - 改进 `modules/chapter_identifier.py` 中的 `_find_title_position` 方法
  - 实现精确匹配、高相似度匹配、子字符串匹配和跨块匹配策略
  - 使用 `difflib.SequenceMatcher` 计算文本相似度
  - 添加综合评分系统，选择最佳匹配
  - 支持识别跨多个连续文本块的标题
  - 解决 "Introduction to Agents and Agent architectures" 被错误识别为 "Agents and Agents" 章节的问题
- 创建测试用例：
  - 创建 `tests/test_title_position_fix.py` 文件，包含6个完整的测试用例
  - 测试精确匹配、避免子字符串误匹配、跨块匹配、高相似度匹配等场景
- 运行测试验证：
  - 6个新测试用例全部通过
  - 12个现有相关测试全部通过
  - 验证实际PDF文件处理正常
- 相关文件：
  - `modules/chapter_identifier.py`
  - `tests/test_title_position_fix.py`

## 2026-03-13

- 优化翻译进度条提示：
  - 在 `services/translation_service.py` 中添加初始阶段进度提示（0%, 5%, 10%）
  - 细化语义合并阶段进度提示（45%, 47%, 50%）
  - 优化输出文件生成阶段进度提示（80%, 90%, 95%, 100%）
  - 确保进度值平滑过渡，消除用户感觉"卡住"的问题
- 增强表格翻译日志：
  - 在表格翻译流程中添加详细的日志记录
  - 记录表格处理、单元格翻译和结果存储的详细信息
  - 提高系统可调试性和问题定位能力
- 实现智能默认章节命名功能：
  - 修改 `chapter_identifier.py`，添加智能命名功能，使用页面第一个文本块作为默认章节名
  - 添加 `use_smart_naming` 和 `max_title_length` 配置参数
  - 实现 `_get_first_text_block()` 方法获取页面第一个文本块
  - 实现 `_truncate_title()` 方法截断长标题
  - 添加 fallback 逻辑：页面无文本块时使用文件名和页号作为标题
- 增强章节识别功能：
  - 改进 `_find_title_position()` 方法，添加精确匹配、高相似度匹配、子字符串匹配和跨块匹配
  - 添加详细的日志记录，提高调试效率
  - 增强文本块、表格和图像的章节关联日志输出
- UI文本优化：
  - 将"按章节拆分Markdown"修改为"按章节翻译Markdown"
  - 优化提示文本为"启用后按章节拆分翻译并生成多个Markdown文件"
  - 修改 `templates/index.html`、`static/js/main.js` 和 `services/translation_service.py` 中的相关文本
- 创建测试用例：
  - 创建 `tests/test_default_chapter.py` 文件，包含14个完整的测试用例
  - 测试默认配置、自定义配置、无章节页面检测、智能命名、固定命名、空页面处理、长标题截断等功能
  - 使用 Mock 技术模拟 PDF 文本提取，确保测试可靠性
- 运行回归测试：
  - 所有14个智能默认章节命名测试用例通过
  - 完整测试套件185个测试用例全部通过
- 相关文件：
  - `services/translation_service.py`
  - `modules/chapter_identifier.py`
  - `templates/index.html`
  - `static/js/main.js`
  - `tests/test_default_chapter.py`

## 2026-03-13

- 实现 PyMuPDF 表格提取功能：
  - 在 `table_processor.py` 中添加 `extract_tables_by_pymupdf` 函数
  - 使用 PyMuPDF 的 `find_tables()` 方法提取表格
  - 保持与 `extract_tables_by_camelot` 相同的参数和返回值格式
  - 修复 bbox 类型判断问题（元组或 Rect 对象）
  - 实现表格边界框计算、单元格信息构建和表格结构分析
- 集成到 PdfExtractor：
  - 添加 `table_extractor` 参数，支持选择 Camelot 或 PyMuPDF
  - 默认使用 PyMuPDF 进行表格提取
  - 在 `__init__.py` 中导出新函数
- UI 文本优化：
  - 将"按章节拆分Markdown"修改为"按章节翻译Markdown"
  - 优化提示文本为"启用后按章节拆分翻译并生成多个Markdown文件"
  - 修改 `index.html`、`main.js` 和 `translation_service.py` 中的相关文本
- 日志增强：
  - 在表格翻译流程中添加详细日志，包括表格处理、单元格翻译和结果存储
  - 在表格绘制流程中添加调试日志，包括表格结构、单元格内容和译文状态
  - 调整日志级别从 DEBUG 为 INFO，提高日志可读性
- 相关文件：
  - `modules/extractors/table_processor.py`
  - `modules/extractors/__init__.py`
  - `modules/pdf_extractor.py`
  - `modules/pdf_generator.py`
  - `services/translation_service.py`
  - `templates/index.html`
  - `static/js/main.js`
  - `utils/logging_config.py`

## 2026-03-12

- 实现语义块合并功能优化：
  - 优化 `merge_semantic_blocks` 函数，添加垂直距离检查（阈值：10单位）
  - 改进句子延续判断逻辑，支持中英文文本
  - 增加章节信息处理，确保同章节的文本块正确合并
  - 修复 `merge_semantic_blocks_with_llm` 函数，添加章节信息支持
  - 调整批量处理大小为10，优化性能
- 实现Markdown生成功能改进：
  - 优化章节内容组织，使用合并块替代原始文本块
  - 实现并行章节Markdown生成，提高处理速度
  - 改进结果对象，添加章节级别的成功/失败状态和警告信息
  - 修复章节索引生成逻辑
- 修复函数参数名：
  - 将 `chapter_split` 参数重命名为 `extract_chapter`，提高代码可读性
  - 更新相关函数调用，确保参数传递正确
- 运行回归测试：
  - 执行完整的测试套件，验证代码变更不破坏现有功能
  - 修复测试用例，确保所有测试都通过
- 相关文件：
  - `utils/text_processing.py`
  - `modules/markdown_generator.py`
  - `modules/pdf_extractor.py`
  - `services/translation_service.py`
  - `tests/test_title_body_separation.py`

## 2026-03-11

- 实现章节Markdown生成功能优化：
  - 修复章节映射逻辑，确保所有页码都能正确关联到对应的章节
  - 优化章节内容组织逻辑，确保章节文件包含完整的文本、图像和表格内容
  - 简化章节内容处理逻辑，提高代码可维护性
  - 添加详细的日志记录，便于调试和问题追踪
- 修复测试用例：
  - 修复`test_same_language_optimization.py`中的参数名错误，将`output_filename`改为`filename`
  - 确保所有测试用例都能正确运行
- 运行回归测试：
  - 执行完整的测试套件，验证代码变更不破坏现有功能
  - 确保所有测试用例都通过，提高代码质量

## 2026-03-06

- 实现术语表文件操作功能：
  - 在Web界面添加"加载术语文件"和"保存术语到文件"按钮，支持从本地文件导入术语表和将当前术语表导出到本地文件
  - 实现文件加载功能，支持.txt术语表文件
  - 实现文件保存功能，将术语表内容导出为文本文件
  - 添加错误处理和用户反馈，确保操作流程顺畅
- 前端界面优化：
  - 缩小按钮高度，使界面更加美观
  - 将"使用大语言模型进行语义判断"选项默认设置为勾选状态，提高翻译质量
  - 优化术语表标题和按钮的布局，使界面更加整洁
- 术语提取服务改进：
  - 支持从PDF中提取表格文本，提高术语提取的完整性
  - 支持指定页码范围提取术语，提高提取效率
  - 优化提取逻辑，确保术语表格式正确
- 翻译服务改进：
  - 增加进度更新和页面处理状态，让用户清楚看到翻译过程
  - 优化多线程翻译逻辑，提高翻译效率
  - 增强错误处理和异常捕获，提高系统稳定性
- 测试和优化：
  - 创建 `tests/test_glossary_file_operations.py` 文件，添加术语表文件操作功能的测试用例
  - 执行完整的回归测试，确保代码变更不破坏现有功能
  - 所有测试用例都通过，确保功能正常工作

## 2026-03-05

- 实现自动术语提取功能：
  - 创建 `modules/glossary_extractor.py` 文件，实现术语提取的抽象基类和具体实现类
  - 支持aiping和硅基流动两个平台的术语提取
  - 实现 `services/glossary_service.py`，提供从PDF中提取术语的服务
  - 在Web界面添加"提取术语"按钮，支持从上传的PDF中自动提取术语表
  - 实现术语提取进度显示，让用户清楚看到提取过程和结果
  - 优化提示词，确保生成的术语表严格按照"术语: 翻译"的格式
- 前端界面优化：
  - 将提取术语的进度条放在了提取术语按钮的同一行右边
  - 确保进度条在提取完成后不自动消失，让用户能够看到结果
  - 在提取完成后隐藏取消按钮，使界面更加简洁
  - 将"从上传的PDF中自动提取术语表"文本放到了提取术语按钮的下面
- 测试和优化：
  - 创建 `tests/test_glossary_extractor.py` 文件，添加术语提取功能的测试用例
  - 执行完整的回归测试，确保代码变更不破坏现有功能
  - 所有测试用例都通过，确保功能正常工作

## 2026-02-28

- 实现结果类型化：
  - 创建 `models/result_types.py` 文件，定义 `TruncationInfo`、`Result`、`OpenAIResult`、`TranslationResult` 和 `MarkdownResult` 类
  - 修改 `aiping_translator.py`，返回 `TranslationResult` 对象而不是字符串
  - 修改 `markdown_generator.py`，返回 `MarkdownResult` 对象而不是字符串
  - 添加 `batch_translate` 方法到 `AipingTranslator` 类
- 优化 API 调用：
  - 在 `config.py` 中添加 `AIPING_EXTRA_BODY` 配置，集中管理费用优先策略参数
  - 修改 `aiping_translator.py`、`aiping_semantic_analyzer.py` 和 `markdown_generator.py`，从配置中读取 `extra_body`
  - 添加流式响应处理、超时检测、token 使用信息捕获和截断检测功能
- 实现截断警告功能：
  - 在 `models/result_types.py` 中实现 `TruncationInfo` 类，用于结构化存储截断信息
  - 在 `services/translation_service.py` 中添加截断检测逻辑，当翻译或 Markdown 生成被截断时添加警告
  - 在前端 `static/js/main.js` 中实现警告显示逻辑，确保用户能够看到截断警告
  - 修复警告显示重复的问题，在任务完成时隐藏进度区域的警告
- 其他优化：
  - 添加详细的日志记录，便于调试和问题追踪
  - 提高代码的可读性和可维护性

## 2026-02-27

- 实现max_tokens属性配置：
  - 为多个模块添加max_tokens属性，支持默认值和外部配置
  - `markdown_generator.py`：添加max_tokens属性，默认值8192
  - `aiping_semantic_analyzer.py`：添加max_tokens（默认1024）和batch_max_tokens（默认2048）属性
  - `aiping_translator.py`：添加max_tokens属性，默认值8192
  - `semantic_analyzer.py`：添加max_tokens（默认1024）和batch_max_tokens（默认2048）属性
  - `silicon_flow_translator.py`：添加max_tokens属性，默认值8192
  - 更新所有API调用使用类属性作为最大token数
  - 创建`test_max_tokens_property.py`测试文件，验证max_tokens属性功能
- 修复Markdown生成中图像URL元素丢失问题：
  - 分析图像URL元素丢失的原因，发现布局模型可能会删除图像URL元素
  - 修改布局提示词，添加"保留图像元素"的规范要求，明确要求布局模型不要删除或修改任何图像URL元素
  - 在`generate_markdown`方法中添加详细的日志记录，用于追踪图像URL在布局模型处理前后的状态
  - 确保图像URL元素在Markdown生成过程中正确保留
- 更新项目文档：
  - 创建`image_url_issue_plan.md`分析计划文件，记录问题分析和解决方案
  - 更新AI开发进度记录，添加2026-02-27的开发记录
  - 确保图像URL元素在Markdown生成过程中正确保留

## 2026-02-26

- 分离语义分析功能：
  - 从Translator类中分离语义分析功能，创建独立的SemanticAnalyzer基类和AipingSemanticAnalyzer派生类
  - 实现SemanticAnalyzerFactory工厂类，用于创建不同类型的语义分析器实例
  - 修改`translation_service.py`，添加`get_semantic_analyzer`方法，用于创建语义分析器实例
  - 更新`merge_semantic_blocks_with_llm`函数，使用`semantic_analyzer`参数替代`translator`参数
  - 确保翻译服务直接调用语义分析器进行语义分析，不再通过翻译器间接调用
- 优化Markdown生成器调用方式：
  - 修改`translation_service.py`中的Markdown生成器创建代码，使用`create_markdown_generator`函数替代直接实例化
  - 添加`create_markdown_generator`函数的导入语句
  - 确保根据选择的翻译API类型自动使用相应的Markdown生成器
  - 支持aiping和silicon_flow两种API类型的Markdown生成
- 验证变更：
  - 运行所有测试用例，确保代码变更不破坏现有功能
  - 验证不同翻译API类型的Markdown生成器都能正确创建和使用
  - 确保所有测试用例通过，提高代码质量

## 2026-02-19

- 新增多线程并行翻译功能：
  - 在`translation_service.py`中添加线程池，用于并行翻译文本块和表格单元格
  - 实现线程安全的结果收集和处理
  - 保持翻译结果的原始顺序
  - 支持表格单元格的并行翻译
- 新增配置参数：
  - 在`config.py`中添加`MAX_WORKERS`参数，控制最大线程数
  - 在`config.py`中添加`TRANSLATION_BATCH_SIZE`参数，控制翻译批处理大小
  - 支持通过环境变量覆盖默认值
- 优化批处理大小：
  - 在`text_processing.py`中将batch_size从5增加到10，提高批量处理效率
- 新增测试用例：
  - 创建`test_thread_safety.py`文件，测试线程安全性
  - 创建`test_performance_multithread.py`文件，测试多线程性能
  - 在`test_translation_service.py`中添加多线程功能测试
- 运行回归测试：
  - 执行所有测试用例，确保代码变更不破坏现有功能
  - 验证多线程功能正常工作
  - 确保所有测试用例通过，提高代码质量

## 2026-02-19

- 新增批量语义分析功能：
  - 在`translator.py`中添加`batch_analyze_semantic_relationship`方法和`_generate_batch_semantic_analysis_prompt`方法
  - 在`aiping_translator.py`中实现批量语义分析功能，支持流式响应和错误处理
  - 在`silicon_flow_translator.py`中实现批量语义分析功能，支持非流式响应和错误处理
  - 优化批量语义分析提示词，提供详细的分析标准和输出要求
- 新增批量语义分析测试用例：
  - 创建`test_batch_semantic_analysis.py`文件，包含完整的批量语义分析测试用例
  - 测试基础功能、错误处理、重试机制和边界情况
  - 确保测试覆盖各种批量语义分析场景
- 新增列表项延续测试：
  - 创建`test_list_item_continuation.py`文件，测试列表项延续的语义分析
- 新增性能测试：
  - 创建`test_performance_batch_analysis.py`文件，测试批量语义分析的性能
- 运行回归测试：
  - 执行所有测试用例，确保代码变更不破坏现有功能
  - 验证批量语义分析功能正常工作
  - 确保所有测试用例通过，提高代码质量

## 2026-02-09

- 优化Word和Markdown生成器图表插入方法：
  - 移除MergedBlock类中的self.bbox属性，简化代码结构
  - 实现基于原始块位置的图表插入方法，提高图表定位准确性
  - 统一Word和Markdown生成器的图表插入逻辑，确保一致性
  - 移除不必要的边框计算和排序代码，简化代码结构
- 修复表格插入位置问题：
  - 修改`translation_service.py`中的`translate_tables`方法，返回PdfTable对象而不是字典
  - 更新`docx_generator.py`中的`_add_table`方法，使用PdfTable对象属性
  - 更新`markdown_generator.py`中的`_convert_table_to_markdown`方法，使用PdfTable对象属性
  - 更新`pdf_generator.py`中的表格处理代码，使用PdfTable对象属性
  - 确保表格边界框信息在整个处理流程中正确保留
- 更新测试用例：
  - 修改`test_markdown_table.py`，使用PdfTable和PdfCell对象
  - 修改`test_pdf_generator.py`的`test_generate_pdf_with_tables`方法，使用PdfTable和PdfCell对象
  - 确保测试用例与代码变更一致，验证表格处理功能
- 运行回归测试：
  - 执行所有测试用例，确保代码变更不破坏现有功能
  - 验证表格和图表插入功能正常工作
  - 确保所有测试用例通过，提高代码质量

## 2026-02-07

- 优化文本连续判断提示词：
  - 修改`translator.py`中的语义分析提示词，添加明确的标题识别规则
  - 详细描述标题的语义特征，如简洁性、概括性、引导性
  - 明确指示LLM不要将标题与其他文本块合并
  - 提供具体的标题示例和非标题示例
- 添加标题识别测试用例：
  - 在`test_semantic_merge_extended.py`中添加TestTitleRecognition类
  - 包含三个测试用例，测试标题不与正文合并、正文不与标题合并、标题不与标题合并
  - 确保测试覆盖各种标题与正文的组合情况
- 优化Markdown生成器提示词：
  - 修改`markdown_generator.py`中的提示词，添加不返回代码块标记的要求
  - 明确指示LLM不要在输出的开头或结尾添加`markdown ` 或任何其他代码块标记
  - 确保生成的Markdown文本格式正确，便于后续处理
- 优化测试用例更新提示词：
  - 重新结构`update_test_case.md`文件，添加详细的测试用例设计原则和最佳实践
  - 提供测试用例示例和失败用例处理流程
  - 增强测试用例维护和管理指南
- 优化文档更新提示词：
  - 重新结构`update_doc.md`文件，添加详细的代码变更分析步骤
  - 提供文档更新指南和最佳实践
  - 增强验证清单和文档更新流程
- 优化回归测试提示词：
  - 重新结构`regression_testing.md`文件，添加详细的回归测试指南
  - 提供测试环境准备、执行流程和结果分析步骤
  - 增强失败用例处理和回归测试最佳实践
- 优化代码提交提示词：
  - 重新结构`submit.md`文件，添加详细的代码提交流程和指南
  - 提供提交信息规范和分支管理建议
  - 增强常见问题处理和提交最佳实践
- 其他优化：
  - 改进前端UI，增加下载按钮的垂直间距
  - 优化错误处理，移除降级方案，直接返回错误提示
  - 确保所有测试用例通过，提高代码质量

## 2026-02-06

- 实现Markdown输出格式：
  - 创建`markdown_generator.py`模块，支持基于布局模型生成Markdown文档
  - 实现表格到Markdown的转换功能，支持正确的表格格式
  - 实现图表位置排序和插入功能，确保图表出现在正确位置
  - 支持文本块内部的元素插入，处理复杂的布局
- 优化Markdown下载功能：
  - 实现Markdown文件和图片的zip包下载
  - 更新前端显示逻辑，确保下载按钮显示正确的文本
  - 确保翻译所有选项包含Markdown下载
- 优化测试配置：
  - 创建pytest.ini配置文件，支持测试类型分离
  - 实现测试服务的自动管理，包括启动和停止
  - 添加Markdown相关的测试文件，覆盖下载、图表位置和表格生成功能
- 更新配置和环境变量：
  - 添加布局模型配置变量
  - 更新环境变量名称，提高清晰度
  - 确保配置系统的一致性

## 2026-02-05

- 修复Word生成图表位置问题：
  - 优化DocxGenerator类，实现按垂直位置排序页面元素
  - 添加表格处理逻辑，按页码组织表格
  - 实现元素在文本块内部的插入功能
  - 改进页面元素的处理顺序，确保图表和表格出现在正确位置
- 清理测试代码：
  - 将`test_style_extraction.py`中的return语句改为assert语句
  - 将`test_same_language_optimization.py`中的return语句改为assert语句
  - 确保所有测试函数使用assert语句进行断言，避免返回值警告
- 更新项目文档：
  - 更新项目规则文档，添加关于模块化开发、优先构建数据模型和少用字典对象的规则
  - 更新项目规则文档，添加详细的代码结构相关规则
  - 更新开发进度文档，添加关于使用对象属性访问语法的记录
- 更新技术栈规范：
  - 移除pdfplumber和百度翻译API
  - 添加camelot-py[cv]、opencv-python、python-docx等依赖
- 更新目录结构：
  - 添加新的目录和文件，移除不存在的目录和文件
  - 反映项目当前的文件组织情况

## 2026-02-04

- 优化系统提示词：
  - 添加规则10：不要翻译URL地址，保持原状
  - 添加规则11：不要翻译代码段，保持原状
- 改进页眉页脚识别逻辑：
  - 将频率阈值从50%提高到70%
  - 添加位置过滤逻辑，只考虑顶部和底部区域的文本
  - 提高页眉页脚识别的准确性
- 添加语义合并开关：
  - 在Web界面添加"启用语义块合并"复选框
  - 在翻译服务中添加`semantic_merge`参数
  - 实现语义合并与非合并两种翻译模式
- 优化语义合并相关代码：
  - 改进`merge_semantic_blocks`函数，计算并记录合并块的最大宽度和高度
  - 优化`process_merged_blocks`和`process_original_blocks`方法
  - 添加语义合并的全面测试覆盖
  - 提高翻译连贯性和质量

## 2026-02-02

- 替换 pdfplumber 为 camelot-py 以改进表格提取
- 实现坐标系转换逻辑，解决 camelot-py 与 PyMuPDF 的坐标系差异
- 更新依赖项，添加 camelot-py[cv]、ghostscript 和 opencv-python
- 修复相关错误和测试用例，确保表格提取功能正常工作
- 更新项目文档，反映技术栈变更
- 优化 PDF 提取器：
  - 修改 `__init__` 方法以接受 `pdf_path` 参数并在初始化时提取元数据
  - 添加 `get_metadata` 方法提取 PDF 元数据
  - 更新提取方法使用实例属性
  - 移除 `extract_page_text` 方法
  - 添加 `total_pages` 属性用于快速获取页数
- 修复 API 超时错误：
  - 为 OpenAI 客户端添加 30 秒超时设置
  - 实现 3 次重试机制，每次间隔 2 秒
- 修复 XML 兼容性错误：
  - 添加 `_clean_xml_compatible_text` 方法移除非 XML 兼容字符
  - 更新文本添加方法使用清理函数
- 其他修复：
  - 在 `table_processor.py` 中添加 os 模块导入
  - 修复异常处理以正确抛出 FileNotFoundError
  - 更新 `translation_service.py` 使用 `total_pages` 属性
  - 添加新测试用例验证 `total_pages` 属性和其他新功能

## 2026-01-28

- 添加翻译模型配置支持：
  - 在.env文件中添加AIPING_MODEL和SILICON_FLOW_MODEL配置
  - 在config.py中添加对应的配置项
  - 更新translation_service.py使用配置的模型参数
  - 支持通过环境变量覆盖默认模型
- 移除翻译器类中的硬编码默认值：
  - 移除aiping_translator.py中的硬编码默认值
  - 移除silicon_flow_translator.py中的硬编码默认值
  - 统一通过配置系统管理默认值
- 删除百度翻译相关代码及选项：
  - 移除config.py中的百度翻译配置
  - 移除.env文件中的百度翻译配置
  - 移除templates/index.html中的百度翻译选项
  - 移除services/translation_service.py中的百度翻译处理逻辑
  - 删除modules/baidu_translator.py文件
  - 移除测试文件中的百度翻译引用
  - 删除tests/test_baidu_translator.py文件
  - 更新README.md移除百度翻译相关内容
- 优化系统提示词和用户提示词：
  - 在translator.py基类中添加_generate_system_prompt和_generate_user_prompt方法
  - 统一提示词格式，消除代码重复
  - 更新aiping_translator.py使用基类提示词生成方法
  - 更新silicon_flow_translator.py使用基类提示词生成方法
- 更新项目文档：
  - 更新README.md中的功能列表和技术栈
  - 更新requirement.md中的翻译API支持情况
  - 更新AI开发进度记录

## 2026-01-27

- 实现Word文档生成功能：
  - 创建docx_generator.py模块，支持基于合并后的翻译结果生成Word文档
  - 添加python-docx依赖到requirements.txt
  - 支持保留原始字体、大小、颜色和样式
  - 支持图片提取和插入到Word文档
  - 支持页面分节和分页符
  - 修复Word文档生成中的空白页问题
- 优化文档样式处理：
  - 修复字体大小问题，确保使用正确的字体大小
  - 修复颜色问题，确保只有正确的文本部分显示为绿色
  - 优化字体样式的继承和应用
- 简化Word生成流程：
  - 只使用合并后的翻译结果生成Word文档
  - 移除使用拆分后结果生成Word的功能
  - 提高生成效率和文档质量
- 添加输出格式选择功能：
  - 在Web界面添加PDF、Word和两者都输出的选项
  - 更新后端逻辑支持多格式输出
  - 确保下载按钮样式一致
- 修复相关问题：
  - 修复Task对象缺少add_attachment方法的问题
  - 优化图片提取和处理逻辑
  - 提高整体系统稳定性

## 2026-01-26

- 修复文本块丢失问题：
  - 修复merge_semantic_blocks函数中合并条件的括号位置错误
  - 原条件逻辑错误导致正文块被错误处理和丢失
  - 修正括号位置后，所有正文块都能正确合并和翻译
- 简化PDF翻译工具工作流程：
  - 在提取文本后直接过滤所有非正文块
  - 简化merge_semantic_blocks函数，移除所有处理非正文块的逻辑
  - 后续合并、拆分和翻译流程只需处理正文块，无需考虑非正文块
  - 提高代码可读性和维护性
- 添加13个新的语义合并扩展测试用例：
  - test_merge_consecutive_body_blocks - 测试连续正文块合并
  - test_merge_blocks_with_sentence_continuation_lowercase - 测试小写字母开头句子延续
  - test_merge_blocks_with_sentence_continuation_punctuation - 测试标点开头句子延续
  - test_no_merge_when_sentence_ends - 测试完整句子结尾不合并
  - test_no_merge_when_vertical_distance_large - 测试垂直距离过大不合并
  - test_merge_multiple_sequential_blocks - 测试多个连续块合并
  - test_empty_blocks_list - 测试空列表输入
  - test_single_block - 测试单个块
  - test_is_sentence_continuation - 测试句子延续检测函数
  - test_split_with_english_words - 测试英文单词完整性保护
  - test_split_with_punctuation_adjustment - 测试标点位置调整
  - test_split_empty_translation - 测试空翻译结果处理
  - test_filter_non_body_blocks - 测试非正文块过滤
- 修复4个失败的测试用例：
  - test_progress.py - 导入错误修复
  - test_font_rendering - PDF生成器格式错误修复
  - test_process_translation_with_page_range - 临时文件问题修复
  - test_translate_api - 测试数据文件路径和patch路径错误修复
- 实现100%测试通过率：
  - 测试总数：98个
  - 通过：98个
  - 失败：0个

## 2026-01-24

- 优化文本拆分逻辑，确保左引号、括号、书名号等成对出现的字符不出现在句尾
- 改进了adjust_split_position函数，添加了对左成对字符的检查
- 增强了split_translated_result函数，确保最终的拆分结果中没有左成对字符出现在块尾
- 添加了辅助函数is_left_pair_character来识别不应该出现在句尾的左成对字符
- 更新了测试脚本，验证了优化效果

## 2026-01-18

- 初始版本发布
- 实现PDF文本提取功能
- 支持aiping、硅基流动翻译API
- 实现PDF生成功能
- 提供Web界面
