# PDF翻译工具

## 项目简介

PDF翻译工具是一个支持多种翻译API的PDF文档翻译工具，支持Web服务/CLI命令行/SKILL方式调用，能够准确提取PDF内容，使用多种翻译服务进行翻译，并生成格式良好的翻译后PDF/Word文档。

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
# 翻译PDF文件，默认使用 aiping 大模型服务，英文翻译成中文，输出为pdf, 不启用语义合并和LLM主义判断
pdftrans translate document.pdf -o translated.pdf

# 指定源语言和目标语言
pdftrans translate document.pdf -s en -t zh -o output.pdf

# 使用指定的翻译服务，比如silicon_flow
pdftrans translate document.pdf -T silicon_flow -o output.pdf

# 翻译指定页码
pdftrans translate document.pdf --pages "1-10,15,20-25" -o output.pdf

# 生成Word文档
pdftrans translate document.pdf -f docx -o output.docx

# 生成Markdown并拆分章节
pdftrans translate document.pdf -f markdown --chapter-split -o output/

# 启用语义合并
pdftrans translate document.pdf --semantic-merge -o output.pdf

# 启用语合并及LLM语义判断
pdftrans translate document.pdf -m -l -f docs -o output.pdf

# 翻译时使用术语表
pdftrans translate document.pdf -g glossary.txt -o output.pdf

# 提取术语表
pdftrans glossary document.pdf -o glossary.txt

# 列出支持的语言
pdftrans list-languages
```

#### 技能集成

PDF翻译工具包含技能集成，并提供增强功能：

- **智能默认值**：自动从输入文件的前100行检测源语言，默认目标语言为中文
- **优化输出**：默认为Markdown格式，启用章节拆分、语义合并和LLM语义判断
- **错误处理**：为常见问题（如权限错误）提供清晰的错误信息

#### 技能使用方法

可以通过**自然语言使用**（在支持skill的AI IDE中，如Trae）：你可以使用自然语言与技能交互，例如：
   - "将这个PDF翻译成中文"
   - "将这个PDF翻译成中文，输出为word文档"
   - "从这个PDF中提取术语表"
   - "列出PDF翻译工具支持的语言"

#### API密钥配置

工具需要翻译服务的API密钥才能正常工作。在 `.env` 文件中配置：

```bash
# .env 文件示例

# aiping API 配置
AIPING_API_KEY=your_aiping_api_key

# 硅基流动 API 配置
SILICON_FLOW_API_KEY=your_silicon_flow_api_key
```

只需配置其中一种翻译服务的API密钥即可使用工具。工具默认使用 aiping 大模型服务。

#### CLI选项

**全局选项：**
- `-v, --verbose` - 显示详细输出
- `--version` - 显示版本信息
- `-h, --help` - 显示帮助信息
- `-o, --output` - 输出文件路径
- `-s, --source` - 源语言代码
- `-t, --target` - 目标语言代码
- `-T, --translator` - 翻译服务
- `-p, --pages` - 页码范围
- `-d, --doc-type` - 文档类型

**translate命令选项：**
- `-o, --output` - 输出文件路径（未指定则自动生成）
- `-f, --format` - 输出格式（pdf/docx/markdown，默认：pdf）
- `-g, --glossary` - 术语表文件路径
- `-m, --semantic-merge` - 启用语义合并
- `-l, --llm-merge` - 使用LLM语义判断
- `-c, --chapter-split` - 按章节拆分输出（仅Markdown格式）

## 许可证

AGPL-3.0

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
