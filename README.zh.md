# PDF翻译工具

## 项目简介

PDF翻译工具是一个支持多种翻译API的PDF文档翻译工具，支持Web服务/CLI命令行/SKILL方式调用，能够准确提取PDF内容，使用多种翻译服务进行翻译，并生成格式良好的翻译后PDF/Word文档。

如果你在使用过程中有任何问题或建议，欢迎在公众号【智践行】或小红书【智践行的小芝】留言，也可以通过Gitee仓库提交Issue或Pull Request，期待与大家一起，把PDF翻译工具打磨得更贴合实际需求！

## 功能特点

### 核心功能

- **PDF文本提取**：支持提取普通文本和表格内容，保留位置信息
- **OCR支持**：支持两种 OCR 引擎
  - **PaddleOCR**（本地引擎）：基于 PP-StructureV3，支持版面分析、文字识别、公式识别和表格提取，需安装 PaddlePaddle
  - **LLM OCR**（云端引擎）：基于 DeepSeek-OCR 等视觉大模型，通过翻译服务 API 调用，无需本地安装 PaddlePaddle，适合无 GPU 或需要更好版面理解的场景
- **多翻译API支持**：
  - aiping 模型调用API
  - 硅基流动 模型调用API
  - 百度千帆 模型调用API
- **文档生成**：
  - PDF生成：基于原始PDF生成翻译后的PDF，保留原始布局和格式
  - Word生成：基于合并后的翻译结果生成Word文档，保留原始字体和样式
  - Markdown生成：基于布局模型生成Markdown文档，支持表格和图像的正确位置插入
- **Web界面**：提供简洁易用的Web界面，支持文件上传、翻译服务选择和结果下载
- **指定页码翻译**：支持翻译指定页码或页码范围，提高翻译效率
- **输出格式选择**：支持选择输出为PDF、Word、Markdown或任意组合
- **自动术语提取**：从上传的PDF中自动提取术语表，支持aiping、硅基流动和百度千帆三个平台

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
- **OCR引擎**：
  - PaddleOCR 3.0+（PP-StructureV3）：用于扫描版PDF文字提取、版面分析、公式识别
  - PaddlePaddle 3.0+：深度学习框架（CPU/GPU自动检测）
- **文档处理**：
  - python-docx：用于Word文档生成
- **翻译API**：aiping翻译API、硅基流动翻译API、百度千帆翻译API
- **API客户端**：openai：用于调用翻译API
- **测试框架**：pytest
- **版本控制**：Git + Gitee

## 安装步骤

### 1. 克隆仓库

Gitee仓库地址：https://gitee.com/chunju/pdfTrans
GitHub仓库地址：https://github.com/chunju-zhong/pdfTrans

```bash
git clone https://gitee.com/chunju/pdfTrans.git
# 或
git clone https://github.com/chunju-zhong/pdfTrans.git

cd pdfTrans
```

### 2. 创建并激活conda环境

```bash
conda env create -f environment.yml
conda activate pdfTrans
```

### 3. 配置环境变量

- 复制`.env.example`文件为`.env`
- 注册平台的账号（三选一）
  - Aiping账号：https://aiping.cn/#?invitation_code=UVSZ6QWRRK
  - 硅基流动账号：https://cloud.siliconflow.cn/i/OFUfQfNj
  - 百度千帆账号：https://cloud.baidu.com/product-s/qianfan_home
- 获得平台成API密钥
- 在`.env`文件中配置平台模型名称及API的密钥

```bash
cp .env.example .env
```

- 编辑.env文件，添加API密钥并配置平台模型名称

```
# aiping API配置
AIPING_API_KEY=your-secret-key
AIPING_API_URL=https://aiping.cn/api/v1
# 指定翻译模型
AIPING_MODEL_TRANSLATION=Qwen3-32B
# 指定Markdown排版模型
AIPING_MODEL_LAYOUT=Qwen3-32B
# 指定术语提取模型
AIPING_MODEL_GLOSSARY=Qwen3-32B

# 硅基流动API配置
SILICON_FLOW_API_KEY=your-secret-key
SILICON_FLOW_API_URL=https://api.siliconflow.cn/v1/
# 指定翻译模型
SILICON_FLOW_MODEL_TRANSLATION=tencent/Hunyuan-MT-7B
# 指定Markdown排版模型
SILICON_FLOW_MODEL_LAYOUT=Qwen/Qwen3-32B
# 指定术语提取模型
SILICON_FLOW_MODEL_GLOSSARY=Qwen/Qwen3-32B

# 百度千帆API配置
QIANFAN_API_KEY=your-secret-key
QIANFAN_API_URL=https://qianfan.baidubce.com/v1
# 指定翻译模型
QIANFAN_MODEL_TRANSLATION=ernie-4.0-8k
# 指定Markdown排版模型
QIANFAN_MODEL_LAYOUT=ernie-4.0-8k
# 指定术语提取模型
QIANFAN_MODEL_GLOSSARY=ernie-4.0-8k

# LLM OCR配置（复用翻译引擎的API Key，仅需指定模型）
AIPING_OCR_LLM_MODEL=DeepSeek-OCR
SILICON_FLOW_OCR_LLM_MODEL=deepseek-ai/DeepSeek-OCR
```

### 4. 安装依赖

```bash 
pip install -r requirements.txt
```

### 5. 安装 PaddlePaddle（OCR支持）

PaddlePaddle 的 CPU 和 GPU 版本互斥，不能同时安装。使用自动检测脚本：

```bash
bash install_paddle.sh
```

或手动安装：

```bash
# CPU版本（默认，适用于所有平台）
pip install paddlepaddle>=3.0.0

# GPU版本（需要 NVIDIA GPU + CUDA 11.8+）
pip install paddlepaddle-gpu>=3.0.0
```

> **注意**：OCR功能需要安装 PaddlePaddle（PaddleOCR引擎）或配置 LLM OCR 模型（LLM OCR引擎）。如两者均未配置，OCR提取功能将不可用。

### 6. 安装 LaTeX（可选，公式高质量渲染）

LaTeX 用于公式的高质量渲染（usetex 模式）。如不安装，系统将自动降级使用 matplotlib mathtext 渲染公式（功能可用，但复杂公式效果较差）。

```bash
# macOS
brew install --cask mactex

# 或仅安装基础版（体积更小）
brew install --cask basictex

# Linux (Ubuntu/Debian)
sudo apt-get install texlive-full

# 或仅安装基础版（体积更小）
sudo apt-get install texlive-latex-base texlive-fonts-recommended
```

> **注意**：安装完成后请确保 `latex` 命令可在终端中直接调用。

## 使用方法

本工具提供 **Web 界面** 和 **命令行（CLI）** 两种独立的使用方式。无需启动 Web 服务即可直接使用命令行。

### 方式一：Web 界面（图形化操作）

#### 启动服务

```bash
python app.py
```

#### 访问界面

- 打开浏览器，访问 `http://localhost:5000`
- 上传PDF文件
- 系统自动检测并显示PDF总页数
- 选择翻译页码范围（可选，默认全选所有页）
  - 支持单个页码（如：1,3,5）
  - 支持页码范围（如：1-5,7-10）
  - 可以混合使用（如：1-3,5,7-9）
- 选择翻译服务和目标语言
- 选择输出格式（PDF、Word、Markdown或任意组合）
- 启用OCR模式（可选）
  - 勾选"启用OCR"可使用OCR引擎提取文字
  - 选择OCR引擎：
    - **PaddleOCR**（本地引擎）：需安装 PaddlePaddle，适合有 GPU 的本地环境
    - **LLM OCR**（云端引擎）：通过 API 调用视觉大模型，无需 PaddlePaddle，适合无 GPU 环境
  - 系统自动检测GPU（PaddleOCR引擎），可用时使用GPU加速
- 点击"翻译"按钮
- 等待翻译完成，下载翻译后的PDF和/或Word文件

---

### 方式二：命令行（CLI，独立使用，无需启动Web服务）

CLI 可用于批量处理和自动化工作流，**不依赖 Web 服务**，可直接在终端运行。

#### 安装

```bash
# 进入项目目录后安装CLI工具
cd pdfTrans  # 替换为实际的项目路径
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

# 翻译藏语文档（bo 为藏语语言代码）
pdftrans translate document.pdf -s bo -t zh -o output.pdf

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

# 启用语义合并及LLM语义判断
pdftrans translate document.pdf -m -l -f docs -o output.pdf

# 启用OCR模式
pdftrans translate document.pdf --ocr -o output.pdf

# 指定OCR引擎和识别语言
pdftrans translate document.pdf --ocr --ocr-engine paddleocr --ocr-lang en -o output.pdf

# 使用 LLM OCR 云端引擎（无需安装 PaddlePaddle）
pdftrans translate document.pdf --ocr --ocr-engine llm -o output.pdf

# 翻译时使用术语表
pdftrans translate document.pdf -g glossary.txt -o output.pdf

# 提取术语表
pdftrans glossary document.pdf -o glossary.txt

# 列出支持的语言
pdftrans list-languages
```

#### CLI 选项参考

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
- `-f, --format` - 输出格式（pdf/docx/markdown/pdf_docx/all，默认：pdf）
- `-g, --glossary` - 术语表文件路径
- `-m, --semantic-merge` - 启用语义合并
- `-l, --llm-merge` - 使用LLM语义判断
- `-c, --chapter-split` - 按章节拆分输出（仅Markdown格式）
- `--ocr` - 启用OCR模式
- `--ocr-engine` - OCR引擎类型：`paddleocr`（本地，需PaddlePaddle）或 `llm`（云端，需API Key），默认：paddleocr
- `--ocr-lang` - OCR识别语言（默认：根据源语言自动选择）
- `--translation-model` - 覆盖翻译模型
- `--layout-model` - 覆盖Markdown排版模型
- `--glossary-model` - 覆盖术语提取模型
- `--ocr-llm-model` - 覆盖LLM OCR模型

---

### 方式三：AI IDE 技能（自然语言调用，无需手动输入命令）

如果你使用支持 Skill 的 AI IDE（如 **Trae**），可以通过**自然语言**直接调用 PDF 翻译工具，AI 会自动帮你组装并执行 CLI 命令。

#### 安装与配置（以 Trae 为例）

1. **安装 Trae IDE**：访问 https://www.trae.com 下载并安装
2. **安装技能**：将本仓库（pdfTrans）下载到你的项目的技能目录下：
   ```
   你的项目/
   └── .trae/
       └── skills/
           └── pdftrans/    ← 将 pdfTrans 代码放入此目录
               ├── SKILL.md   ← Trae 通过此文件识别并激活技能
               ├── cli.py
               └── ...
   ```
3. **激活技能**：Trae 会自动识别 `SKILL.md` 文件，在对话窗口中即可直接使用 PDF 翻译技能

> **说明**：技能通过 `SKILL.md` 调用 CLI 命令来执行翻译任务。只需确保 `.env` 中已配置 API 密钥（见上方「**3. 配置环境变量**」）。

#### 使用方式

在 AI IDE 的对话窗口中，用自然语言描述你的需求即可，例如：

- "将这个 PDF 翻译成中文"
- "将这个 PDF 翻译成中文，输出为 Word 文档"
- "翻译第 1-10 页，使用 silicon_flow 翻译服务"
- "从这个 PDF 中提取术语表"
- "列出 PDF 翻译工具支持的语言"

#### 技能增强功能

通过技能调用时，AI 会自动提供以下增强：

- **智能默认值**：自动从输入文件的前 100 行检测源语言，默认目标语言为中文
- **优化输出**：默认为 Markdown 格式，启用章节拆分、语义合并和 LLM 语义判断
- **错误处理**：为常见问题（如权限错误）提供清晰的错误信息

> **说明**：技能模式通过 `SKILL.md` 调用 CLI 命令执行翻译，请确保已按上方**安装步骤**完成环境配置（conda 环境、依赖安装、API 密钥），并能正常运行 `pdftrans --help` 命令。

## 许可证

AGPL-3.0

## 联系方式

如果你在使用过程中有任何问题或建议，欢迎在公众号【智践行】或小红书【智践行的小芝】里留言，也可以通过Gitee仓库提交Issue或Pull Request，我们期待与大家一起，把PDF翻译工具打磨得更贴合实际需求！

## 更新日志

项目更新日志已移动到单独的 [docs/CHANGELOG.zh.md](docs/CHANGELOG.zh.md) 文件中。

## 任务列表

项目任务列表请查看 [docs/TODO.md](docs/TODO.md) 文件。

## 注意事项

1. OCR模式提供增强的文字提取，支持版面分析、公式和表格识别（需安装PaddlePaddle或配置LLM OCR）
2. 翻译质量取决于所选翻译API的质量
3. 处理大型PDF文档可能需要较长时间，可使用指定翻译页功能分次翻译
4. 请确保正确配置API密钥，否则翻译功能将无法使用
