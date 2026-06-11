# PaddlePaddle GPU/CPU 自动选择安装 + README 更新 OCR 使用说明 Spec

## Why

当前 `requirements.txt` 中 `paddlepaddle`（CPU）和 `paddlepaddle-gpu`（GPU）是互斥安装的，用户需要手动选择。需要安装脚本根据硬件自动选择正确的包。同时，项目已新增 PaddleOCR 支持，但 README（中英文版本）仍标注"不支持OCR"，需要更新 OCR 功能说明和安装步骤。

## What Changes

- **修改 `requirements.txt`**：将 `paddlepaddle` 和 `paddlepaddle-gpu` 都注释掉，添加说明
- **新增安装脚本 `install_paddle.sh`**：自动检测 GPU 是否可用，安装对应的 PaddlePaddle 版本
- **更新 `README.md`（英文版）**：添加 OCR 功能说明、安装步骤、Web 和 CLI 使用说明
- **更新 `README.zh.md`（中文版）**：同步更新 OCR 功能说明、安装步骤、Web 和 CLI 使用说明

## Impact

- Affected files: `requirements.txt`、新增 `install_paddle.sh`、`README.md`、`README.zh.md`
- Affected code: 无代码变更

## ADDED Requirements

### Requirement: 自动检测硬件安装对应 PaddlePaddle 版本

系统 SHALL 提供安装脚本，自动检测 GPU 是否可用，安装对应的 PaddlePaddle 版本。

#### Scenario: 有 NVIDIA GPU 的环境

- **WHEN** 系统检测到 NVIDIA GPU 且 CUDA 可用
- **THEN** 安装 `paddlepaddle-gpu`

#### Scenario: 无 GPU 的环境（CPU only）

- **WHEN** 系统未检测到 NVIDIA GPU 或 CUDA 不可用
- **THEN** 安装 `paddlepaddle`（CPU 版本）

#### Scenario: macOS 环境

- **WHEN** 系统是 macOS
- **THEN** 安装 `paddlepaddle`（CPU 版本，因为 PaddlePaddle GPU 不支持 macOS）

### Requirement: README 更新 OCR 功能说明

中英文 README SHALL 更新以下内容：

1. **移除"不支持OCR"的说明**：当前两个 README 都标注"本工具仅支持非扫描版PDF文档，不支持OCR功能"，需要移除
2. **添加 OCR 功能说明**：在核心功能中添加 PaddleOCR 支持
3. **更新安装步骤**：添加 `install_paddle.sh` 安装说明
4. **更新 Web 使用说明**：说明 OCR 模式选项
5. **更新 CLI 使用说明**：说明 `--ocr`、`--ocr-engine`、`--ocr-lang` 选项
6. **添加 GPU 加速说明**：说明 `OCR_USE_GPU` 环境变量配置

## MODIFIED Requirements

### Requirement: requirements.txt 中 PaddlePaddle 依赖声明

`requirements.txt` 中 SHALL 将 PaddlePaddle 包注释掉，并添加说明指向安装脚本。

## REMOVED Requirements

### Requirement: README 中"不支持OCR"的说明

**Reason**: 项目已支持 PaddleOCR
**Migration**: 替换为 OCR 功能说明

## 技术说明

### PaddlePaddle CPU 和 GPU 包不能同时安装

`paddlepaddle` 和 `paddlepaddle-gpu` 在 pip 中是互斥的，两者都安装 `paddle` 包到同一命名空间，同时安装会导致冲突。

### OCR 功能的 Web 和 CLI 使用方式

**Web 端**：
- 上传 PDF 后，勾选"启用OCR"选项
- 可选择 OCR 引擎（当前仅支持 PaddleOCR）
- 系统自动检测 GPU 并选择设备

**CLI 端**：
- `--ocr`：启用 OCR 模式
- `--ocr-engine paddleocr`：指定 OCR 引擎
- `--ocr-lang en`：指定 OCR 识别语言

**GPU 加速**：
- 环境变量 `OCR_USE_GPU=true` 启用 GPU 加速
- 安装 `paddlepaddle-gpu` 后自动使用 GPU
- macOS 不支持 GPU 加速

### 代码中的 GPU 检测已正确

`paddle_extractor.py` 的 `_check_gpu_available()` 已正确使用 `paddle.is_compiled_with_cuda()` 检测：
- 安装 `paddlepaddle`（CPU）→ `is_compiled_with_cuda()` 返回 `False`
- 安装 `paddlepaddle-gpu`（GPU）→ `is_compiled_with_cuda()` 返回 `True`
