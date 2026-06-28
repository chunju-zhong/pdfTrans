# pdfTrans 开发指南

## 1. 环境要求与搭建

### 1.1 系统要求

- **Python**: 3.9+（推荐 3.9，与 `environment.yml` 一致）
- **操作系统**: macOS / Linux / Windows
- **内存**: 建议 8GB 以上（OCR 模式建议 16GB）
- **GPU**: 可选，NVIDIA GPU + CUDA 11.8+ 可加速 PaddleOCR

### 1.2 Conda 环境创建

```bash
# 使用 environment.yml 创建 conda 环境
conda env create -f environment.yml

# 激活环境
conda activate pdftrans
```

`environment.yml` 定义了以下核心依赖：

| 依赖 | 安装方式 | 说明 |
|------|----------|------|
| python=3.9 | conda | Python 版本 |
| flask | conda | Web 框架 |
| requests | conda | HTTP 请求库 |
| python-dotenv | conda | 环境变量加载 |
| ghostscript | conda | PDF/图像处理工具 |
| pymupdf | pip | PDF 解析库 |
| camelot-py[cv] | pip | PDF 表格提取 |
| opencv-python | pip | 图像处理 |

### 1.3 pip 依赖安装

如果不使用 conda，可直接通过 pip 安装：

```bash
pip install -r requirements.txt
```

`requirements.txt` 包含的完整依赖：

| 依赖 | 用途 |
|------|------|
| flask | Web 服务 |
| pymupdf | PDF 文本和页面提取 |
| camelot-py[cv] | PDF 表格提取 |
| ghostscript | camelot 依赖的 Ghostscript |
| opencv-python | 图像处理 |
| requests | HTTP 请求 |
| python-dotenv | .env 文件加载 |
| openai | OpenAI 兼容 API 客户端 |
| pytest | 测试框架 |
| python-docx | Word 文档生成 |
| matplotlib | 图表渲染 |
| latex2mathml | LaTeX 转 MathML（公式渲染） |
| psutil | 系统资源监控 |
| paddleocr[all]>=3.0.0 | PaddleOCR 完整依赖（含 PP-StructureV3） |

### 1.4 PaddlePaddle 安装

PaddlePaddle 不能同时安装 CPU 和 GPU 版本，请使用安装脚本自动选择：

```bash
bash install_paddle.sh
```

脚本逻辑：
1. **macOS** → 自动安装 CPU 版本（macOS 不支持 GPU）
2. **Linux 无 NVIDIA GPU** → 安装 CPU 版本
3. **Linux 有 NVIDIA GPU + CUDA ≥ 11.8** → 安装 GPU 版本
4. **Linux 有 NVIDIA GPU + CUDA < 11.8** → 安装 CPU 版本

手动安装：

```bash
# CPU 版本
pip install "paddlepaddle>=3.0.0"

# GPU 版本（需要 NVIDIA GPU + CUDA）
pip install "paddlepaddle-gpu>=3.0.0"
```

验证安装：

```bash
python -c 'import paddle; print(paddle.__version__)'
```

### 1.5 .env 文件配置

```bash
# 从模板复制
cp .env.example .env

# 编辑配置
vim .env
```

**必须配置**：至少配置一种翻译服务的 API 密钥（`AIPING_API_KEY`、`SILICON_FLOW_API_KEY` 或 `QIANFAN_API_KEY`），以及 `SECRET_KEY`。

### 1.6 平台注意事项

| 平台 | 注意事项 |
|------|----------|
| **macOS** | PaddleOCR 默认使用 CPU；Intel 16GB Mac 可能需要启用 `OCR_SKIP_TABLE=true` 节省内存 |
| **Linux** | 支持 GPU 加速；需安装 CUDA 驱动 |
| **Windows** | 需手动安装 Ghostscript 并加入 PATH；部分路径处理可能需要调整 |

---

## 2. 配置说明

所有配置通过 `.env` 文件或环境变量设置，由 `config.py` 中的 `Config` 类加载。

### 2.1 Flask 配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `SECRET_KEY` | Flask 密钥，用于会话安全 | 无（未设置则启动报错） | **是** |
| `DEBUG` | 调试模式 | `False` | 否 |

### 2.2 aiping API 配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `AIPING_API_KEY` | aiping API 密钥 | 无 | 使用 aiping 时必填 |
| `AIPING_API_URL` | aiping API 地址 | `https://aiping.cn/api/v1` | 否 |
| `AIPING_MODEL_TRANSLATION` | 翻译模型 | `Qwen3-32B` | 否 |
| `AIPING_MODEL_LAYOUT` | Markdown 排版模型 | `Qwen3-32B` | 否 |
| `AIPING_MODEL_GLOSSARY` | 术语提取模型 | `Qwen3-32B` | 否 |

### 2.3 硅基流动 API 配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `SILICON_FLOW_API_KEY` | 硅基流动 API 密钥 | 无 | 使用 silicon_flow 时必填 |
| `SILICON_FLOW_API_URL` | 硅基流动 API 地址 | `https://api.siliconflow.cn/v1` | 否 |
| `SILICON_FLOW_MODEL_TRANSLATION` | 翻译模型 | `tencent/Hunyuan-MT-7B` | 否 |
| `SILICON_FLOW_MODEL_LAYOUT` | Markdown 排版模型 | `Qwen/Qwen3-32B` | 否 |
| `SILICON_FLOW_MODEL_GLOSSARY` | 术语提取模型 | `Qwen/Qwen3-32B` | 否 |

### 2.4 百度千帆 API 配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `QIANFAN_API_KEY` | 百度千帆 API 密钥 | 无 | 使用 qianfan 时必填 |
| `QIANFAN_API_URL` | 百度千帆 API 地址 | `https://qianfan.baidubce.com/v2` | 否 |
| `QIANFAN_MODEL` | 翻译模型 | 无 | 否 |
| `QIANFAN_MODEL_LAYOUT` | Markdown 排版模型 | 无 | 否 |
| `QIANFAN_MODEL_GLOSSARY` | 术语提取模型 | 无 | 否 |
| `QIANFAN_OCR_LLM_MODEL` | 千帆 LLM OCR 模型 | 无 | 否 |
| `QIANFAN_EXTRA_BODY` | 千帆 API extra_body 参数（JSON） | `{}` | 否 |

> **代码级默认值**：当 `QIANFAN_EXTRA_BODY` 环境变量未设置时，代码使用类级别默认值 `{"enable_thinking": False, "thinking": {"type": "disabled"}}`，同时关闭 Qwen3 系列（`enable_thinking`）和 GLM-4.5+/5.x 系列（`thinking.type`）的思考模式。详见 [ARCHITECTURE.zh.md](ARCHITECTURE.zh.md) 7.3 节。

### 2.5 OCR 配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `USE_OCR` | 是否默认启用 OCR | `false` | 否 |
| `OCR_ENGINE` | OCR 引擎类型 | `paddleocr` | 否 |
| `OCR_LANGUAGE` | OCR 识别语言 | `ch` | 否 |
| `OCR_USE_GPU` | 是否使用 GPU 加速 | macOS=`false`，其他=`true` | 否 |
| `OCR_PADDLE_DPI` | PaddleOCR 渲染 DPI（内存优化） | `120`（激进优化）/ `150`（质量优先） | 否 |
| `OCR_SKIP_TABLE` | 跳过表格识别（节省内存） | `false` | 否 |
| `OCR_SKIP_FORMULA` | 跳过公式识别（节省内存） | `false` | 否 |

### 2.6 OCR 超时与重试配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `OCR_HEARTBEAT_TIMEOUT` | 心跳超时（秒），0=禁用 | `0` | 否 |
| `OCR_MAX_TOTAL_TIME` | OCR 最大总执行时间（秒） | `252000` | 否 |
| `OCR_STALL_TIMEOUT` | OCR 进度停滞超时（秒） | `1800` | 否 |
| `OCR_MAX_RETRIES` | 子进程崩溃后最大重试次数 | `2` | 否 |
| `OCR_RETRY_BACKOFF` | 重试间隔（秒），每次递增 1.5 倍 | `5.0` | 否 |
| `OCR_DYNAMIC_PARAMS` | 根据系统负载动态调整 OCR 参数 | `true` | 否 |

### 2.7 翻译配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `MAX_WORKERS` | 最大线程数 | `8` | 否 |
| `TRANSLATION_BATCH_SIZE` | 翻译批处理大小 | `10` | 否 |
| `USE_TWO_PHASE_MERGE` | 是否使用两阶段并行合并 | `true` | 否 |
| `MERGE_MAX_WORKERS` | 并行合并的最大线程数 | `5` | 否 |
| `MERGE_BATCH_SIZE` | 每批处理的文本对数量 | `20` | 否 |

### 2.8 LLM OCR 配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `AIPING_OCR_LLM_MODEL` | aiping LLM OCR 模型 | `DeepSeek-OCR` | 否 |
| `SILICON_FLOW_OCR_LLM_MODEL` | 硅基流动 LLM OCR 模型 | `deepseek-ai/DeepSeek-OCR` | 否 |
| `QIANFAN_OCR_LLM_MODEL` | 百度千帆 LLM OCR 模型 | 无 | 否 |
| `OCR_LLM_MAX_TOKENS` | LLM OCR 最大 token 数 | `8192` | 否 |
| `OCR_LLM_TEMPERATURE` | LLM OCR 温度 | `0.1` | 否 |
| `OCR_LLM_DPI` | LLM OCR 渲染 DPI | `150` | 否 |

### 2.9 按模块 API 参数配置

每个翻译服务支持按模块覆盖翻译、排版、术语提取的模型和温度参数：

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `TRANSLATION_TEMPERATURE` | 翻译温度参数 | `0.1` | 否 |
| `SEMANTIC_ANALYSIS_TEMPERATURE` | 语义分析温度参数 | `0.1` | 否 |
| `GLOSSARY_TEMPERATURE` | 术语提取温度参数 | `0.1` | 否 |
| `LAYOUT_TEMPERATURE` | Markdown 排版温度参数 | `0.1` | 否 |

这些参数为所有翻译器共用。CLI 参数（`--translation-model`、`--layout-model`、`--glossary-model`、`--ocr-llm-model`）可覆盖 `.env` 中的默认模型设置。

### 2.10 其他配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `DEFAULT_DOC_TYPE` | 默认文档类型 | `AI技术` | 否 |

支持的文档类型：`AI技术`、`技术文档`、`商务文档`、`学术论文`、`法律文档`、`医学文档`

---

## 3. 运行方式

### 3.1 Web 服务

```bash
python app.py
```

- **默认端口**: 5000
- **自定义端口**: `python app.py --port 8080`
- **浏览器访问**: `http://127.0.0.1:5000`
- **上传限制**: 500MB

### 3.2 CLI 命令行

```bash
# 基本翻译
python cli.py translate document.pdf

# 指定语言和翻译服务
python cli.py translate document.pdf -s en -t zh -T silicon_flow

# 指定页码范围和输出格式
python cli.py translate document.pdf --pages "1-10,15" -f docx

# 启用语义合并和 LLM 合并
python cli.py translate document.pdf -m -l

# 启用 OCR 模式
python cli.py translate document.pdf --ocr --ocr-engine paddleocr
```

### 3.3 AI IDE Skill

`SKILL.md` 是 AI IDE（如 Trae、Cursor 等）的技能描述文件，定义了 pdftrans 工具的能力和调用方式。

- **作用**: 让 AI IDE 理解 pdftrans 的功能，自动根据用户需求选择合适的参数
- **默认行为**: 未指定输出格式时默认 Markdown（按章节切分），默认启用语义合并和 LLM 合并
- **调用方式**: AI IDE 读取 SKILL.md 后，自动将用户自然语言请求转换为 CLI 命令

---

## 4. CLI 完整命令参考

### 4.1 `pdftrans translate <input>` — 翻译 PDF 文件

| 参数 | 短形式 | 类型 | 说明 | 默认值 | 必填 |
|------|--------|------|------|--------|------|
| `input` | — | 位置参数 | 输入 PDF 文件路径 | — | **是** |
| `--output` | `-o` | str | 输出文件路径 | 自动生成 | 否 |
| `--source` | `-s` | str | 源语言代码 | `en` | 否 |
| `--target` | `-t` | str | 目标语言代码 | `zh` | 否 |
| `--translator` | `-T` | str | 翻译服务类型：`aiping`/`silicon_flow`/`qianfan` | `aiping` | 否 |
| `--translation-model` | — | str | 覆盖翻译模型（优先于配置文件默认值） | 无 | 否 |
| `--layout-model` | — | str | 覆盖 Markdown 排版模型 | 无 | 否 |
| `--glossary-model` | — | str | 覆盖术语提取模型 | 无 | 否 |
| `--ocr-llm-model` | — | str | 覆盖 LLM OCR 模型 | 无 | 否 |
| `--pages` | `-p` | str | 页码范围，如 `"1-5,7,9-10"` | 全部页面 | 否 |
| `--format` | `-f` | str | 输出格式：`pdf`/`docx`/`markdown`/`pdf_docx`/`all` | `pdf` | 否 |
| `--glossary` | `-g` | str | 术语表文件路径 | 无 | 否 |
| `--doc-type` | `-d` | str | 文档类型或领域说明 | `AI技术` | 否 |
| `--semantic-merge` | `-m` | flag | 启用语义合并 | `False` | 否 |
| `--llm-merge` | `-l` | flag | 使用 LLM 语义判断 | `False` | 否 |
| `--chapter-split` | `-c` | flag | 按章节拆分输出 Markdown（仅 Markdown 格式有效） | `False` | 否 |
| `--ocr` | — | flag | 启用 OCR 模式提取扫描版 PDF | `False` | 否 |
| `--ocr-engine` | — | str | OCR 引擎：`paddleocr`/`llm` | `paddleocr` | 否 |
| `--ocr-lang` | — | str | OCR 识别语言 | 根据源语言自动选择 | 否 |

**输出格式说明**：
- `pdf` → 生成双语对照 PDF
- `docx` → 生成 Word 文档
- `markdown` → 生成 Markdown 文件（打包为 `.zip`）
- `pdf_docx` → 同时生成 PDF 和 Word 文档
- `all` → 同时生成 PDF、Word 和 Markdown

**智能后缀处理**：工具会根据输出格式自动添加正确的文件后缀（`.pdf`、`.docx`、`.zip`）。

### 4.2 `pdftrans glossary <input>` — 提取术语表

| 参数 | 短形式 | 类型 | 说明 | 默认值 | 必填 |
|------|--------|------|------|--------|------|
| `input` | — | 位置参数 | 输入 PDF 文件路径 | — | **是** |
| `--output` | `-o` | str | 输出文件路径 | 自动生成 `glossary_<name>.txt` | 否 |
| `--source` | `-s` | str | 源语言代码 | `en` | 否 |
| `--target` | `-t` | str | 目标语言代码 | `zh` | 否 |
| `--translator` | `-T` | str | 翻译服务类型 | `aiping` | 否 |
| `--pages` | `-p` | str | 页码范围 | 全部页面 | 否 |
| `--doc-type` | `-d` | str | 文档类型或领域说明 | `AI技术` | 否 |

### 4.3 `pdftrans list-languages` — 列出支持的语言

无额外参数。显示所有支持的语言代码和名称。

### 4.4 全局选项

| 参数 | 短形式 | 说明 |
|------|--------|------|
| `--verbose` | `-v` | 显示详细输出 |
| `--version` | — | 显示版本号（1.0.0） |

---

## 5. Web API 接口参考

### 5.1 GET /

主页路由，渲染翻译界面。

**响应**: HTML 页面，包含以下模板变量：
- `supported_languages` — 支持的语言列表
- `default_source` — 默认源语言
- `default_target` — 默认目标语言
- `default_translator` — 默认翻译服务
- `default_doc_type` — 默认文档类型

### 5.2 POST /translate

提交翻译任务（异步）。

**请求参数**（`multipart/form-data`）：

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `pdf_file` | file | PDF 文件（必填） | — |
| `source_lang` | str | 源语言代码 | `en` |
| `target_lang` | str | 目标语言代码 | `zh` |
| `translator` | str | 翻译服务：`aiping`/`silicon_flow`/`qianfan` | `silicon_flow` |
| `doc_type` | str | 文档类型 | `AI技术` |
| `glossary` | str | 术语表内容 | 空 |
| `page_range` | str | 页码范围 | 空 |
| `output_format` | str | 输出格式 | `pdf` |
| `semantic_merge` | str | 启用语义合并（`"on"` 启用） | 空 |
| `use_llm_merging` | str | 使用 LLM 合并（`"on"` 启用） | 空 |
| `chapter_split` | str | 按章节拆分（`"on"` 启用） | 空 |
| `ocr_mode` | str | 启用 OCR（`"on"` 启用） | 空 |
| `ocr_engine` | str | OCR 引擎 | `paddleocr` |

**响应**：

```json
{
  "success": true,
  "task_id": "uuid-string",
  "message": "翻译任务已启动"
}
```

### 5.3 GET /progress/\<task_id\>

轮询翻译任务进度。

**响应**：

```json
{
  "success": true,
  "task_id": "uuid-string",
  "status": "processing",
  "progress": 65,
  "message": "正在翻译...",
  "result_file": "translated_xxx.pdf",
  "attachments": [],
  "error": null,
  "canceled": false,
  "warnings": [],
  "total_time": 120
}
```

### 5.4 POST /cancel/\<task_id\>

取消翻译任务。

**响应**：

```json
{
  "success": true,
  "message": "翻译任务已取消"
}
```

### 5.5 GET /download/\<filename\>

下载页面路由，渲染下载界面。

**参数**：`filename` — 文件名（仅允许字母数字、下划线、连字符、点号）

### 5.6 GET /download_file/\<filename\>

实际文件下载路由。

**参数**：`filename` — 文件名（仅允许字母数字、下划线、连字符、点号）

**响应**: 从 `OUTPUT_FOLDER` 目录发送文件附件。

### 5.7 POST /get_pdf_pages

获取 PDF 文件的总页数。

**请求参数**（`multipart/form-data`）：

| 参数 | 类型 | 说明 |
|------|------|------|
| `pdf_file` | file | PDF 文件（必填） |

**响应**：

```json
{
  "success": true,
  "total_pages": 42
}
```

### 5.8 POST /extract_glossary

提取术语表（异步）。

**请求参数**（`multipart/form-data`）：

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `pdf_file` | file | PDF 文件（必填） | — |
| `source_lang` | str | 源语言代码 | `en` |
| `target_lang` | str | 目标语言代码 | `zh` |
| `translator` | str | 翻译服务 | `aiping` |
| `page_range` | str | 页码范围（最大 1000 字符） | 空 |
| `doc_type` | str | 文档类型 | `AI技术` |

**响应**：

```json
{
  "success": true,
  "task_id": "uuid-string",
  "message": "术语提取任务已启动"
}
```

### 5.9 GET /glossary_progress/\<task_id\>

获取术语提取任务进度。

**响应**：

```json
{
  "success": true,
  "task_id": "uuid-string",
  "status": "processing",
  "progress": 50,
  "message": "正在提取术语...",
  "glossary": "",
  "error": null
}
```

### 5.10 POST /glossary_cancel/\<task_id\>

取消术语提取任务。

**响应**：

```json
{
  "success": true,
  "message": "术语提取任务已取消"
}
```

---

## 6. 测试方法

### 6.1 运行测试

```bash
# 运行所有测试（排除慢速测试）
pytest

# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 运行端到端测试
pytest -m e2e

# 运行慢速测试
pytest -m slow

# 运行指定测试文件
pytest tests/test_translator.py

# 运行指定测试类/方法
pytest tests/test_translator.py::TestTranslator::test_translate

# 显示详细输出
pytest -v

# 显示打印输出
pytest -s
```

### 6.2 pytest 配置

`pytest.ini` 中的配置：

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: 单元测试，不依赖外部服务
    integration: 集成测试，依赖外部服务
    e2e: 端到端测试，依赖完整的系统
    slow: 慢速测试，含time.sleep或长时间运行
addopts = --ignore=tests/test_simple_pdf_gen.py -m "not slow"
```

### 6.3 测试目录结构

```
tests/
├── conftest.py              # 公共 fixture
├── data/                    # 测试数据
│   └── test_data_en_text.pdf
├── test_app.py              # Web 应用测试
├── test_cli.py              # CLI 命令测试
├── test_translator.py       # 翻译器基类测试
├── test_aiping_translator.py    # aiping 翻译器测试
├── test_silicon_flow_translator.py  # 硅基流动翻译器测试
├── test_translation_service.py    # 翻译服务测试
├── test_pdf_extractor.py    # PDF 提取器测试
├── test_pdf_generator.py    # PDF 生成器测试
├── test_pdf_page_translation.py   # PDF 页面翻译测试
├── test_ocr_extractor.py    # OCR 提取器测试
├── test_ocr_worker.py       # OCR Worker 测试
├── test_llm_ocr.py          # LLM OCR 测试
├── test_llm_extractor_*.py  # LLM 提取器系列测试
├── test_markdown_generator.py     # Markdown 生成器测试
├── test_markdown_table.py   # Markdown 表格测试
├── test_markdown_chart_position.py  # Markdown 图表位置测试
├── test_markdown_download.py     # Markdown 下载测试
├── test_docx_generator.py   # Word 文档生成器测试
├── test_semantic_merge.py   # 语义合并测试
├── test_semantic_merge_extended.py  # 语义合并扩展测试
├── test_semantic_merge_optimization.py  # 语义合并优化测试
├── test_semantic_analyzer.py     # 语义分析器测试
├── test_batch_semantic_analysis.py   # 批量语义分析测试
├── test_glossary_extractor.py    # 术语提取器测试
├── test_glossary_extraction.py   # 术语提取测试
├── test_glossary_file_operations.py  # 术语文件操作测试
├── test_chapter_*.py        # 章节相关测试
├── test_table_*.py          # 表格相关测试
├── test_text_splitting.py   # 文本拆分测试
├── test_text_analyzer.py    # 文本分析器测试
├── test_progress.py         # 进度管理测试
├── test_thread_safety.py    # 线程安全测试
└── ...
```

### 6.4 公共 Fixture（conftest.py）

| Fixture 名称 | 说明 |
|--------------|------|
| `test_pdf_path` | 测试 PDF 文件路径（`tests/data/test_data_en_text.pdf`） |
| `invalid_pdf_path` | 不存在的 PDF 文件路径 |
| `mock_translator_response` | 模拟的翻译 API 响应 |
| `sample_text` | 示例英文文本 |
| `source_lang` | 源语言代码（`"en"`） |
| `target_lang` | 目标语言代码（`"zh"`） |
| `sample_translated_text` | 示例翻译文本 |

---

## 7. 常见开发任务指南

### 7.1 添加新翻译 API

以添加名为 `new_provider` 的翻译服务为例：

**步骤 1：创建翻译器子类**

在 `modules/` 下创建 `new_provider_translator.py`：

```python
from modules.translator import Translator
from models.result_types import TranslationResult, TruncationInfo

class NewProviderTranslator(Translator):
    """NewProvider 翻译器"""

    def __init__(self, api_key, api_url=None, model=None):
        super().__init__(api_key, api_url)
        self.model = model or 'default-model'

    def translate(self, text, source_lang, target_lang, doc_type, glossary):
        # 检查源语言与目标语言是否一致
        result = super().translate(text, source_lang, target_lang, doc_type, glossary)
        if result is not None:
            return result

        # 实现具体的翻译逻辑
        # 1. 生成系统提示词（可复用基类的 _generate_system_prompt）
        # 2. 调用 API
        # 3. 返回 TranslationResult 对象
        ...
```

**步骤 2：注册到 TranslationService**

在 `services/translation_service.py` 的 `get_translator()` 方法中添加：

```python
elif translator_type == 'new_provider':
    if not config.NEW_PROVIDER_API_KEY:
        raise ValueError("NewProvider 翻译 API 配置不完整")
    return NewProviderTranslator(
        config.NEW_PROVIDER_API_KEY,
        config.NEW_PROVIDER_API_URL,
        config.NEW_PROVIDER_MODEL
    )
```

**步骤 3：添加配置**

在 `config.py` 中添加：

```python
NEW_PROVIDER_API_KEY = os.environ.get('NEW_PROVIDER_API_KEY')
NEW_PROVIDER_API_URL = os.environ.get('NEW_PROVIDER_API_URL') or 'https://api.newprovider.com/v1'
NEW_PROVIDER_MODEL = os.environ.get('NEW_PROVIDER_MODEL') or 'default-model'
```

在 `.env.example` 中添加对应变量。

**步骤 4：更新 CLI 选项**

在 `cli.py` 的 translate 子命令中更新 `--translator` 的 `choices`：

```python
choices=['aiping', 'silicon_flow', 'new_provider']
```

### 7.2 添加新 OCR 引擎

**步骤 1：创建 OCR 提取器子类**

在 `modules/ocr/` 下创建 `new_engine_extractor.py`：

```python
from modules.ocr.base import OcrExtractor

class NewEngineOcrExtractor(OcrExtractor):
    """新 OCR 引擎提取器"""

    def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None):
        # 实现具体的 OCR 提取逻辑
        # 返回 PdfExtraction 对象（结构与 PdfExtractor.extract() 一致）
        ...
```

**步骤 2：注册到工厂函数**

在 `modules/ocr/factory.py` 中添加：

```python
SUPPORTED_OCR_ENGINES = ['paddleocr', 'llm', 'new_engine']

def create_ocr_extractor(ocr_type='paddleocr', **kwargs):
    if ocr_type == 'paddleocr':
        ...
    elif ocr_type == 'llm':
        ...
    elif ocr_type == 'new_engine':
        from modules.ocr.new_engine_extractor import NewEngineOcrExtractor
        return NewEngineOcrExtractor(**kwargs)
    else:
        raise ValueError(...)
```

**步骤 3：添加配置和 CLI 选项**

在 `config.py` 和 `cli.py` 中添加相应配置。

### 7.3 添加新输出格式

**步骤 1：创建生成器类**

在 `modules/` 下创建新的生成器，如 `html_generator.py`。

**步骤 2：在 TranslationService 中集成**

在 `services/translation_service.py` 中添加新格式的生成逻辑分支。

**步骤 3：添加格式选项**

在 `cli.py` 的 `--format` 参数的 `choices` 中添加新格式，在 Web 前端中添加对应选项。

### 7.4 修改翻译 Prompt

翻译 Prompt 定义在 `modules/translator.py` 的 `_generate_system_prompt()` 方法中，采用4节结构化设计：

| 节编号 | 节名称 | 内容概要 |
|-------|--------|---------|
| 一 | 核心原则 | 语义连贯、自然过渡、风格一致、简洁精炼 |
| 二 | 语义与风格 | 术语一致、不增删义、语法正确、技术精准 |
| 三 | 保持格式 | 不翻译 URL、保留代码格式、长度控制、不翻译公式、不解释缩写、保持列表格式、保留单元格分隔符 `|||` |
| 四 | 禁止元注释 | 不输出元注释或原文 |

提示词通过 `rule_registry.merge_into_prompt()` 注入语言专项规则（见 `prompts/rule_registry.py` 和 `prompts/language_rules/`），支持按翻译方向动态扩展。

**修改注意事项**：
- 修改 Prompt 后务必运行翻译测试验证效果
- 节之间有相互约束关系，修改一节可能影响其他节的效果
- 建议通过 `--glossary` 参数和 `doc_type` 参数微调，而非直接修改核心规则
- 添加语言专项规则时，在 `prompts/language_rules/` 下创建对应模块，而非修改核心提示词

### 7.5 添加新语言

**步骤 1：更新 `config.py` 中的 `SUPPORTED_LANGUAGES`**

```python
SUPPORTED_LANGUAGES = {
    'zh': '中文',
    'en': '英语',
    'ja': '日语',
    'ko': '韩语',
    'fr': '法语',
    'de': '德语',
    'es': '西班牙语',
    'ru': '俄语',
    'pt': '葡萄牙语',  # 新增
}
```

**步骤 2：更新 CLI 选项**

在 `cli.py` 的 `--source` 和 `--target` 参数的 `choices` 中添加新语言代码。

**步骤 3：更新翻译器基类**

在 `modules/translator.py` 的 `supported_languages` 字典中添加新语言。

**步骤 4：更新 OCR 语言映射**

如果使用 OCR 模式，需在 OCR 引擎中添加新语言对应的识别语言代码。

**步骤 5：添加语言专项规则（可选）**

如果新语言需要特殊翻译规则（如藏文的敬语规则、特殊断句规则等），在 `prompts/language_rules/` 目录下创建规则模块：

```python
# prompts/language_rules/xx_to_yy.py

RULES = """
[语言专项规则内容]
"""
```

然后在 `prompts/rule_registry.py` 中注册该规则，使其在对应翻译方向时通过 `merge_into_prompt()` 自动注入。

---

## 8. 代码规范与约定

### 8.1 工厂模式

项目中广泛使用工厂模式创建不同类型的实例：

| 工厂 | 文件 | 支持的类型 |
|------|------|-----------|
| OCR 提取器工厂 | `modules/ocr/factory.py` | `paddleocr`、`llm` |
| Markdown 生成器工厂 | `modules/markdown_generator.py`（`create_markdown_generator()`） | `aiping`、`silicon_flow` |
| 语义分析器工厂 | `modules/semantic_analyzer_factory.py` | `aiping`、`silicon_flow` |
| 翻译器工厂 | `services/translation_service.py`（`get_translator()`） | `aiping`、`silicon_flow`、`qianfan` |

### 8.2 策略模式

翻译器和 OCR 引擎采用策略模式，通过统一的基类接口实现可替换：

- **翻译器**: `Translator` 基类 → `AipingTranslator`、`SiliconFlowTranslator`、`QianfanTranslator`
- **OCR 引擎**: `OcrExtractor` 基类 → `PaddleOcrExtractor`、`LlmOcrExtractor`

### 8.3 子进程隔离

PaddleOCR 在独立子进程中运行（`modules/ocr/ocr_worker.py`），避免 GIL 和内存泄漏影响主进程。关键机制：

- 子进程通过队列通信传递结果
- 支持心跳检测和超时处理
- 子进程崩溃后自动重试（最多 `OCR_MAX_RETRIES` 次）

### 8.4 并行处理

使用 `ThreadPoolExecutor` 实现并行处理：

- **翻译**: 多线程并行翻译文本块
- **术语提取**: 多线程并行提取术语
- **Markdown 章节生成**: 多线程并行生成各章节文件

线程数由 `MAX_WORKERS`（默认 8）控制。

### 8.5 优雅降级

| 场景 | 降级策略 |
|------|---------|
| 翻译失败 | 回退到原文 |
| 公式渲染失败 | 降级为纯文本显示 |
| 文本溢出 | 自动缩小字号或截断 |
| OCR 子进程崩溃 | 自动重试（最多 2 次） |
| Markdown 布局模型失败 | 抛出异常（不使用降级方案） |

### 8.6 进度管理

基于 `PHASE_CONFIG` 的细粒度进度追踪，定义在 `models/phase_config.py`：

**翻译任务阶段**：

| 阶段 ID | 名称 | 进度范围 |
|---------|------|---------|
| `init` | 初始化 | 0% - 5% |
| `extraction` | 文本图表提取 | 5% - 40% |
| `semantic_merge` | 语义合并 | 40% - 50% |
| `translation` | 文本翻译 | 50% - 85% |
| `table_translation` | 表格翻译 | 85% - 92% |
| `generation` | 生成输出 | 92% - 98% |
| `clean` | 清理临时文件 | 98% - 100% |

**术语提取阶段**：

| 阶段 ID | 名称 | 进度范围 |
|---------|------|---------|
| `init` | 开始提取 | 0% - 5% |
| `pdf_extraction` | 文本提取 | 5% - 30% |
| `term_extraction` | 术语提取 | 30% - 100% |

### 8.7 任务取消

通过 `Task.canceled` 标志实现任务取消：

- Web 端：`POST /cancel/<task_id>` 设置 `canceled=True`
- CLI 端：`KeyboardInterrupt` 触发取消
- 各处理阶段定期检查 `canceled` 标志，及时退出

### 8.8 日志规范

```python
from utils.logging_config import get_logger

logger = get_logger(__name__)
```

- 使用 `get_logger(__name__)` 获取模块级 logger
- 不使用 `print()` 输出调试信息
- Web 模式下 werkzeug HTTP 日志级别设为 ERROR

### 8.9 错误分类

OCR 模块定义了两种错误类型：

- **`OcrRetryableError`**: 可重试错误（如子进程崩溃、超时），自动重试
- **`OcrFatalError`**: 致命错误（如文件不存在、参数无效），直接失败

---

## 9. 支持语言列表

| 语言代码 | 语言名称 |
|---------|---------|
| `zh` | 中文 |
| `en` | 英语 |
| `ja` | 日语 |
| `ko` | 韩语 |
| `fr` | 法语 |
| `de` | 德语 |
| `es` | 西班牙语 |
| `ru` | 俄语 |
| `bo` | 藏文 |

默认源语言：`en`（英语）
默认目标语言：`zh`（中文）
