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
- **自动术语提取**：从上传的PDF中自动提取术语表，支持aiping和硅基流动两个平台

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
  - camelot-py\[cv]：用于表格提取
  - opencv-python：camelot-py\[cv]的依赖
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

### 命令行使用

该工具现已支持命令行界面（CLI），可用于批量处理和自动化工作流。

#### 安装

```bash
# 安装CLI工具
pip install -e .

# 或直接运行，无需安装
python cli.py --help
```

#### 基本命令

```bash
# 翻译PDF文件
pdftrans translate document.pdf -o translated.pdf

# 指定源语言和目标语言
pdftrans translate document.pdf -s en -t zh -o output.pdf

# 使用指定的翻译服务
pdftrans translate document.pdf -T silicon_flow -o output.pdf

# 翻译指定页码
pdftrans translate document.pdf --pages "1-10,15,20-25" -o output.pdf

# 生成Word文档
pdftrans translate document.pdf -f docx -o output.docx

# 生成Markdown并拆分章节
pdftrans translate document.pdf -f markdown --chapter-split -o output/

# 使用术语表
pdftrans translate document.pdf -g glossary.txt -o output.pdf

# 启用语义合并
pdftrans translate document.pdf --semantic-merge -o output.pdf

# 提取术语表
pdftrans glossary document.pdf -o glossary.txt

# 列出支持的语言
pdftrans list-languages
```

#### 技能集成

PDF翻译工具包含技能集成，提供增强功能：

- **智能默认值**：自动从输入文件的前100行检测源语言，默认目标语言为中文
- **优化输出**：默认为Markdown格式，启用章节拆分、语义合并和LLM合并
- **智能后缀处理**：根据输出格式自动添加正确的文件后缀
- **错误处理**：为常见问题（如权限错误）提供清晰的错误信息

#### 技能使用方法

技能可以通过以下方式使用：

1. **基本翻译**：只需提供PDF文件路径，技能会自动检测源语言并翻译为中文
   ```bash
   pdftrans translate document.pdf
   ```

2. **指定输出格式**：技能默认为Markdown格式，但你可以指定其他格式
   ```bash
   pdftrans translate document.pdf -f pdf
   pdftrans translate document.pdf -f docx
   ```

3. **使用章节拆分**：对于Markdown输出，技能会自动启用章节拆分
   ```bash
   pdftrans translate document.pdf -f markdown
   ```

4. **启用语义合并**：技能会自动启用语义合并和LLM合并，以获得更好的翻译质量
   ```bash
   pdftrans translate document.pdf -m -l
   ```

5. **提取术语表**：技能还支持从PDF文件中提取术语表
   ```bash
   pdftrans glossary document.pdf
   ```

6. **列出支持的语言**：查看支持的语言列表
   ```bash
   pdftrans list-languages
   ```

#### 输出目录和临时文件

- **输出目录**：使用 `-o` 参数时，工具会直接在指定的目录中生成输出文件。如果未指定输出目录，将使用默认的 `outputs/` 目录。

- **临时文件**：工具会在输出目录中自动创建一个临时子目录，用于存储提取的图像和Markdown文件等中间文件。这确保了即使在权限受限的沙箱模式下，图像提取也能正常工作。

- **Markdown处理**：对于Markdown输出，工具首先在临时目录中生成Markdown文件，然后在启用章节拆分时将它们打包成zip文件。

#### API密钥配置

工具需要翻译服务的API密钥才能正常工作。在 `.env` 文件中配置：

```bash
# .env 文件示例

# aiping API 配置
AIPING_API_KEY=your_aiping_api_key

# 硅基流动 API 配置
SILICON_FLOW_API_KEY=your_silicon_flow_api_key
```

只需配置其中一种翻译服务的API密钥即可使用工具。

#### CLI选项

**全局选项：**
- `-v, --verbose` - 显示详细输出
- `--version` - 显示版本信息
- `-h, --help` - 显示帮助信息

**translate命令选项：**
- `-o, --output` - 输出文件路径（未指定则自动生成）
- `-s, --source` - 源语言代码（默认：en）
- `-t, --target` - 目标语言代码（默认：zh）
- `-T, --translator` - 翻译服务（aiping/silicon_flow，默认：aiping）
- `-p, --pages` - 页码范围（例如："1-5,7,9-10"）
- `-f, --format` - 输出格式（pdf/docx/markdown，默认：pdf）
- `-g, --glossary` - 术语表文件路径
- `-d, --doc-type` - 文档类型或领域说明（默认：AI技术）
- `-m, --semantic-merge` - 启用语义合并
- `-l, --llm-merge` - 使用LLM合并
- `-c, --chapter-split` - 按章节拆分输出（仅Markdown格式）

**glossary命令选项：**
- `-o, --output` - 输出文件路径
- `-s, --source` - 源语言代码
- `-t, --target` - 目标语言代码
- `-T, --translator` - 翻译服务
- `-p, --pages` - 页码范围
- `-d, --doc-type` - 文档类型

#### 支持的语言

- `zh` - 中文
- `en` - 英语
- `ja` - 日语
- `ko` - 韩语
- `fr` - 法语
- `de` - 德语
- `es` - 西班牙语
- `ru` - 俄语

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

项目更新日志已移动到单独的 [docs/CHANGELOG.zh.md](docs/CHANGELOG.zh.md) 文件中。

## 任务列表

项目任务列表请查看 [docs/TODO.md](docs/TODO.md) 文件。

## 注意事项

1. 本工具仅支持非扫描版PDF文档，不支持OCR功能
2. 翻译质量取决于所选翻译API的质量
3. 处理大型PDF文档可能需要较长时间，可使用指定翻译页功能分次翻译
4. 请确保正确配置API密钥，否则翻译功能将无法使用
