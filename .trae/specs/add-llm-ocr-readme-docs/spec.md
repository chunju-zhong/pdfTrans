# README 增加 LLM OCR 说明和公式工具安装说明 Spec

## Why

当前 README（中英文）缺少以下重要内容的说明：
1. **LLM OCR 模式**：项目支持两种 OCR 引擎（PaddleOCR 本地引擎 + LLM OCR 云端引擎），但 README 仅提及 PaddleOCR，未说明 LLM OCR 的使用方式、配置和适用场景
2. **外部公式工具**：项目依赖系统安装的 `latex` 命令用于高质量公式渲染（usetex 模式），但安装步骤中未提及此依赖

## What Changes

### 变更 1：README.zh.md 功能特点增加 LLM OCR 说明
- 在「核心功能」的 OCR 支持条目中补充 LLM OCR 云端引擎说明
- 明确两种引擎的差异：PaddleOCR（本地，需安装 PaddlePaddle）vs LLM OCR（云端，需 API Key）

### 变更 2：README.zh.md 安装步骤增加公式工具说明
- 在步骤 5（PaddlePaddle 安装）之后新增步骤 6：可选安装 LaTeX（公式高质量渲染）
- 说明不安装时的降级行为（matplotlib mathtext 渲染）

### 变更 3：README.zh.md 使用方法增加 LLM OCR 使用说明
- Web 界面：勾选启用 OCR 后可选择「LLM OCR（云端引擎）」
- CLI：`--ocr-engine llm` 参数
- 配置项：`.env` 中 `AIPING_OCR_LLM_MODEL` / `SILICON_FLOW_OCR_LLM_MODEL`

### 变更 4：README.md 同步更新英文版
- 与中文版对应的所有变更保持一致

## Impact
- Affected code: 无代码变更，仅文档更新
- Affected files: `README.zh.md`, `README.md`

## ADDED Requirements

### Requirement: LLM OCR 功能说明覆盖
README 中必须包含以下信息：
- LLM OCR 是云端 OCR 引擎选项，使用 DeepSeek-OCR 等视觉模型
- 通过翻译服务 API 调用，无需本地安装 PaddlePaddle
- 适用场景：无 GPU / 不想安装 PaddlePaddle / 需要更好的版面理解
- Web 界面选择方式：OCR 引擎下拉框选「LLM OCR（云端引擎）」
- CLI 使用方式：`--ocr-engine llm`
- 环境变量配置：`AIPING_OCR_LLM_MODEL`、`SILICON_FLOW_OCR_LLM_MODEL`

### Requirement: 公式工具安装说明覆盖
README 安装步骤中必须包含：
- LaTeX 为可选依赖，用于高质量公式渲染（usetex 模式）
- 安装方式：TeX Live 或 MacTeX（含 `latex` 命令）
- 不安装时的降级行为：自动使用 matplotlib mathtext 渲染（功能可用但复杂公式效果较差）

## MODIFIED Requirements

### Requirement: OCR 支持条目扩展
原有 OCR 支持条目从仅提及 PaddleOCR 扩展为同时说明两种引擎及其差异。
