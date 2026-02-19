# PDF翻译工具

## 项目简介
PDF翻译工具是一个支持多种翻译API的PDF文档翻译工具，能够准确提取PDF内容，使用多种翻译服务进行翻译，并生成格式良好的翻译后PDF/Word文档。

如果你在使用过程中有任何问题或建议，欢迎在公众号【智践行】留言，也可以通过Gitee仓库提交Issue或Pull Request，期待与大家一起，把PDF翻译工具打磨得更贴合实际需求！

## 功能特点

### 核心功能
- **PDF文本提取**：支持提取普通文本和表格内容，保留位置信息
- **多翻译API支持**：
  - aiping 模型调用API
  - 硅基流动 模型调用API
- **文档生成**：
  - PDF生成：基于原始PDF生成翻译后的PDF，保留原始布局和格式
  - Word生成：基于合并后的翻译结果生成Word文档，保留原始字体和样式
  - Markdown生成：基于布局模型生成Markdown文档，支持表格和图像的正确位置插入
- **Web界面**：提供简洁易用的Web界面，支持文件上传、翻译服务选择和结果下载
- **指定页码翻译**：支持翻译指定页码或页码范围，提高翻译效率
- **输出格式选择**：支持选择输出为PDF、Word、Markdown或任意组合

### 技术特点
- **虚拟环境管理**：支持conda虚拟环境
- **模块化设计**：清晰的代码结构，便于维护和扩展
- **API密钥安全**：使用环境变量管理API密钥，避免硬编码
- **错误处理**：友好的错误提示和处理机制

## 技术栈

- **开发语言**：Python 3.9+
- **虚拟环境**：conda
- **Web框架**：Flask 3.0+
- **PDF处理**：
  - PyMuPDF (fitz) 1.23+：用于PDF文本提取和生成
  - camelot-py[cv]：用于表格提取
  - opencv-python：camelot-py[cv]的依赖
- **文档处理**：
  - python-docx：用于Word文档生成
- **翻译API**：aiping翻译API、硅基流动翻译API
- **API客户端**：openai：用于调用翻译API
- **测试框架**：pytest
- **版本控制**：Git + Gitee

## 安装步骤

### 1. 克隆仓库
```bash
git clone https://gitee.com/chunju/pdfTrans.git
cd pdfTrans
```

### 2. 创建并激活conda环境
```bash
conda env create -f environment.yml
conda activate pdfTrans
```

### 3. 配置环境变量
- 复制`.env.example`文件为`.env`
- 在`.env`文件中配置各翻译或模型调用API的密钥

```bash
cp .env.example .env
# 编辑.env文件，添加API密钥
```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 启动Web服务
```bash
python app.py
```

### 访问Web界面
- 打开浏览器，访问 `http://localhost:5000`
- 上传PDF文件
- 系统自动检测并显示PDF总页数
- 选择翻译页码范围（可选，默认全选所有页）
  - 支持单个页码（如：1,3,5）
  - 支持页码范围（如：1-5,7-10）
  - 可以混合使用（如：1-3,5,7-9）
- 选择翻译服务和目标语言
- 选择输出格式（PDF、Word、Markdown或任意组合）
- 点击"翻译"按钮
- 等待翻译完成，下载翻译后的PDF和/或Word文件

### 命令行使用（可选）
目前暂不支持命令行直接使用，后续将添加该功能。

## 项目结构

```
pdfTrans/
├── .trae/
│   ├── documents/           # 文档目录
│   │   └── ai_dev_progress.md # 开发进度记录文件
│   ├── rules/
│   │   └── project_rules.md # 项目规则文件
│   └── tmp/                 # AI辅助开发生成的代码/数据分析脚本和相关数据
├── .git/                    # Git仓库目录
├── .gitignore               # Git忽略文件
├── app.py                   # Flask应用入口，仅包含Flask应用初始化和路由
├── requirements.txt         # 依赖库列表
├── environment.yml          # conda环境配置
├── config.py                # 配置文件
├── .env.example             # 环境变量示例文件
├── README.md                # 项目说明文档
├── pytest.ini               # pytest配置文件
├── docs/                    # 项目文档目录
├── models/                  # 数据模型
│   ├── task.py              # 任务数据模型
│   ├── text_block.py        # 文本块模型
│   ├── merged_block.py      # 合并块模型
│   └── extraction.py        # 提取模型
├── services/                # 业务逻辑服务
│   ├── task_service.py      # 任务管理服务
│   └── translation_service.py # 翻译业务服务
├── utils/                   # 辅助工具
│   ├── text_processing.py   # 文本处理工具
│   ├── logging_config.py    # 日志配置
│   └── file_utils.py        # 文件处理工具
├── modules/                 # 核心功能模块
│   ├── extractors/          # 提取器模块
│   │   ├── __init__.py
│   │   ├── coordinate_utils.py
│   │   ├── page_utils.py
│   │   ├── style_analyzer.py
│   │   ├── table_processor.py
│   │   └── text_analyzer.py
│   ├── pdf_extractor.py     # PDF提取模块
│   ├── pdf_generator.py     # PDF生成模块
│   ├── docx_generator.py    # Word生成模块
│   ├── markdown_generator.py # Markdown生成模块
│   ├── translator.py        # 翻译基类
│   ├── aiping_translator.py # aiping翻译模块
│   └── silicon_flow_translator.py # 硅基流动翻译模块
├── prompt/                  # 提示词目录
├── temp_images/             # 临时图片目录
├── tests/                   # 测试脚本目录
│   ├── test_*.py            # 测试脚本
├── static/                  # 静态资源
│   ├── css/                 # CSS样式文件
│   │   └── style.css
│   └── js/                  # JavaScript文件
│       └── main.js
├── templates/               # 模板文件
│   ├── index.html           # 主页面模板
│   └── download.html        # 下载页面模板
├── uploads/                 # 上传文件目录
└── outputs/                 # 输出文件目录
```

## 开发流程

### 分支管理
- **main**：主分支，仅用于发布稳定版本
- **develop**：开发分支，整合各功能分支
- **feature/xxx**：功能分支，用于开发新功能
- **bugfix/xxx**：bug修复分支
- **release/xxx**：发布分支，用于准备发布

### 代码提交规范
- 提交信息格式：`[类型] 简短描述`
- 类型包括：feat（新功能）、fix（bug修复）、docs（文档）、style（代码风格）、refactor（重构）、test（测试）、chore（构建/工具）
- 示例：`feat: 添加百度翻译API封装`

### 测试规范
- 所有测试脚本必须放在`tests/`目录下，命名格式为`test_*.py`
- 使用pytest框架进行测试
- 单元测试覆盖率不低于80%

### 运行测试
#### 安装依赖
pytest已包含在requirements.txt中，执行安装依赖命令即可：
```bash
pip install -r requirements.txt
```

#### 运行测试命令
- 运行所有测试：
  ```bash
  pytest
  ```

- 运行特定模块测试：
  ```bash
  pytest tests/test_pdf_extractor.py
  ```

- 运行测试并生成覆盖率报告：
  ```bash
  pytest --cov=modules/ tests/
  ```

#### 测试文件列表
- `test_pdf_extractor.py`：PDF提取模块测试
- `test_translator.py`：翻译基类测试
- `test_aiping_translator.py`：aiping翻译测试
- `test_silicon_flow_translator.py`：硅基流动翻译测试
- `test_pdf_generator.py`：PDF生成模块测试
- `test_markdown_download.py`：Markdown下载测试
- `test_markdown_chart_position.py`：Markdown图表位置测试
- `test_markdown_table.py`：Markdown表格测试
- `conftest.py`：测试配置文件

## 贡献指南

1. Fork仓库
2. 创建功能分支：`git checkout -b feature/xxx`
3. 提交代码：`git commit -m "feat: 添加xxx功能"`
4. 推送分支：`git push origin feature/xxx`
5. 提交Pull Request

## 许可证

MIT License

## 联系方式
如果你在使用过程中有任何问题或建议，欢迎在公众号【智践行】留言，也可以通过Gitee仓库提交Issue或Pull Request，我们期待与大家一起，把PDF翻译工具打磨得更贴合实际需求！

## 更新日志

### 2026-02-19
- 新增多线程并行翻译功能：
  - 在translation_service.py中添加线程池，用于并行翻译文本块和表格单元格
  - 实现线程安全的结果收集和处理
  - 保持翻译结果的原始顺序
  - 支持表格单元格的并行翻译
- 新增配置参数：
  - 在config.py中添加MAX_WORKERS参数，控制最大线程数
  - 在config.py中添加TRANSLATION_BATCH_SIZE参数，控制翻译批处理大小
  - 支持通过环境变量覆盖默认值
- 优化批处理大小：
  - 在text_processing.py中将batch_size从5增加到10，提高批量处理效率
- 新增测试用例：
  - 创建test_thread_safety.py文件，测试线程安全性
  - 创建test_performance_multithread.py文件，测试多线程性能
  - 在test_translation_service.py中添加多线程功能测试
- 运行回归测试：
  - 执行所有测试用例，确保代码变更不破坏现有功能
  - 验证多线程功能正常工作
  - 确保所有测试用例通过，提高代码质量

### 2026-02-19
- 新增批量语义分析功能：
  - 在translator.py中添加batch_analyze_semantic_relationship方法和_generate_batch_semantic_analysis_prompt方法
  - 在aiping_translator.py中实现批量语义分析功能，支持流式响应和错误处理
  - 在silicon_flow_translator.py中实现批量语义分析功能，支持非流式响应和错误处理
  - 优化批量语义分析提示词，提供详细的分析标准和输出要求
- 新增批量语义分析测试用例：
  - 创建test_batch_semantic_analysis.py文件，包含完整的批量语义分析测试用例
  - 测试基础功能、错误处理、重试机制和边界情况
  - 确保测试覆盖各种批量语义分析场景
- 新增列表项延续测试：
  - 创建test_list_item_continuation.py文件，测试列表项延续的语义分析
- 新增性能测试：
  - 创建test_performance_batch_analysis.py文件，测试批量语义分析的性能
- 运行回归测试：
  - 执行所有测试用例，确保代码变更不破坏现有功能
  - 验证批量语义分析功能正常工作
  - 确保所有测试用例通过，提高代码质量

### 2026-02-09
- 优化Word和Markdown生成器图表插入方法：
  - 移除MergedBlock类中的self.bbox属性，简化代码结构
  - 实现基于原始块位置的图表插入方法，提高图表定位准确性
  - 统一Word和Markdown生成器的图表插入逻辑，确保一致性
  - 移除不必要的边框计算和排序代码，简化代码结构
- 修复表格插入位置问题：
  - 修改translation_service.py中的translate_tables方法，返回PdfTable对象而不是字典
  - 更新docx_generator.py中的_add_table方法，使用PdfTable对象属性
  - 更新markdown_generator.py中的_convert_table_to_markdown方法，使用PdfTable对象属性
  - 更新pdf_generator.py中的表格处理代码，使用PdfTable对象属性
  - 确保表格边界框信息在整个处理流程中正确保留
- 更新测试用例：
  - 修改test_markdown_table.py，使用PdfTable和PdfCell对象
  - 修改test_pdf_generator.py的test_generate_pdf_with_tables方法，使用PdfTable和PdfCell对象
  - 确保测试用例与代码变更一致，验证表格处理功能
- 运行回归测试：
  - 执行所有测试用例，确保代码变更不破坏现有功能
  - 验证表格和图表插入功能正常工作
  - 确保所有测试用例通过，提高代码质量

### 2026-02-07
- 优化文本连续判断提示词：
  - 修改translator.py中的语义分析提示词，添加明确的标题识别规则
  - 详细描述标题的语义特征，如简洁性、概括性、引导性
  - 明确指示LLM不要将标题与其他文本块合并
  - 提供具体的标题示例和非标题示例
- 添加标题识别测试用例：
  - 在test_semantic_merge_extended.py中添加TestTitleRecognition类
  - 包含三个测试用例，测试标题不与正文合并、正文不与标题合并、标题不与标题合并
  - 确保测试覆盖各种标题与正文的组合情况
- 优化Markdown生成器提示词：
  - 修改markdown_generator.py中的提示词，添加不返回代码块标记的要求
  - 明确指示LLM不要在输出的开头或结尾添加```markdown ```或任何其他代码块标记
  - 确保生成的Markdown文本格式正确，便于后续处理
- 优化测试用例更新提示词：
  - 重新结构update_test_case.md文件，添加详细的测试用例设计原则和最佳实践
  - 提供测试用例示例和失败用例处理流程
  - 增强测试用例维护和管理指南
- 优化文档更新提示词：
  - 重新结构update_doc.md文件，添加详细的代码变更分析步骤
  - 提供文档更新指南和最佳实践
  - 增强验证清单和文档更新流程
- 优化回归测试提示词：
  - 重新结构regression_testing.md文件，添加详细的回归测试指南
  - 提供测试环境准备、执行流程和结果分析步骤
  - 增强失败用例处理和回归测试最佳实践
- 优化代码提交提示词：
  - 重新结构submit.md文件，添加详细的代码提交流程和指南
  - 提供提交信息规范和分支管理建议
  - 增强常见问题处理和提交最佳实践
- 其他优化：
  - 改进前端UI，增加下载按钮的垂直间距
  - 优化错误处理，移除降级方案，直接返回错误提示
  - 确保所有测试用例通过，提高代码质量

### 2026-02-06
- 实现Markdown输出格式：
  - 创建markdown_generator.py模块，支持基于布局模型生成Markdown文档
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

### 2026-02-05
- 修复Word生成图表位置问题：
  - 优化DocxGenerator类，实现按垂直位置排序页面元素
  - 添加表格处理逻辑，按页码组织表格
  - 实现元素在文本块内部的插入功能
  - 改进页面元素的处理顺序，确保图表和表格出现在正确位置
- 清理测试代码：
  - 将test_style_extraction.py中的return语句改为assert语句
  - 将test_same_language_optimization.py中的return语句改为assert语句
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

### 2026-02-04
- 优化系统提示词：
  - 添加规则10：不要翻译URL地址，保持原状
  - 添加规则11：不要翻译代码段，保持原状
- 改进页眉页脚识别逻辑：
  - 将频率阈值从50%提高到70%
  - 添加位置过滤逻辑，只考虑顶部和底部区域的文本
  - 提高页眉页脚识别的准确性
- 添加语义合并开关：
  - 在Web界面添加"启用语义块合并"复选框
  - 在翻译服务中添加semantic_merge参数
  - 实现语义合并与非合并两种翻译模式
- 优化语义合并相关代码：
  - 改进merge_semantic_blocks函数，计算并记录合并块的最大宽度和高度
  - 优化process_merged_blocks和process_original_blocks方法
  - 添加语义合并的全面测试覆盖
  - 提高翻译连贯性和质量

### 2026-02-02
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
  - 在 table_processor.py 中添加 os 模块导入
  - 修复异常处理以正确抛出 FileNotFoundError
  - 更新 translation_service.py 使用 `total_pages` 属性
  - 添加新测试用例验证 `total_pages` 属性和其他新功能

### 2026-01-28
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

### 2026-01-27
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

### 2026-01-26
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

### 2026-01-24
- 优化文本拆分逻辑，确保左引号、括号、书名号等成对出现的字符不出现在句尾
- 改进了adjust_split_position函数，添加了对左成对字符的检查
- 增强了split_translated_result函数，确保最终的拆分结果中没有左成对字符出现在块尾
- 添加了辅助函数is_left_pair_character来识别不应该出现在句尾的左成对字符
- 更新了测试脚本，验证了优化效果

### 2026-01-18
- 初始版本发布
- 实现PDF文本提取功能
- 支持aiping、硅基流动翻译API
- 实现PDF生成功能
- 提供Web界面

## 注意事项

1. 本工具仅支持非扫描版PDF文档，不支持OCR功能
2. 翻译质量取决于所选翻译API的质量
3. 处理大型PDF文档可能需要较长时间，可使用指定翻译页功能分次翻译
4. 请确保正确配置API密钥，否则翻译功能将无法使用
