# 修复OCR导致Flask后台崩溃 Spec

## Why

用户在使用OCR功能时，Flask后台进程意外退出，导致翻译任务中断。问题出现在PaddleOCR初始化阶段，进程无错误日志直接退出。

## What Changes

- 修复 `config.py` 中 `OCR_USE_GPU` 默认值，在 macOS 上默认使用 CPU
- 在 `paddle_extractor.py` 中添加 GPU 可用性检测，自动回退到 CPU
- 添加更详细的错误日志，捕获 PaddleOCR 初始化异常

## Impact

- Affected specs: OCR功能
- Affected code: `config.py`, `modules/ocr/paddle_extractor.py`

## Root Cause Analysis

### 问题1：Flask Debug 模式 + PaddleOCR 冲突

Flask 在 debug 模式下使用 Werkzeug reloader，会 fork 子进程运行应用。PaddleOCR 在 fork 后初始化模型时可能失败，导致进程静默退出。

**证据**：
- 终端输出显示 `Restarting with stat` 和 `Debugger is active!`
- 进程退出时无错误日志

### 问题2：GPU 配置错误

macOS 上安装的是 `paddlepaddle`（CPU版），但配置默认 `OCR_USE_GPU=True`，导致尝试使用不存在的 GPU。

**证据**：
- 终端输出：`The specified device (GPU) is not available! Switching to CPU instead.`
- `pip show paddlepaddle` 显示安装的是 CPU 版本

### 问题3：异常处理不足

`paddle_extractor.py` 中 `pipeline` 属性初始化时没有捕获 PaddleOCR 的异常，导致异常向上传播时进程崩溃。

## ADDED Requirements

### Requirement: GPU 自动检测与回退

系统 SHALL 在初始化 PaddleOCR 时自动检测 GPU 可用性，在 GPU 不可用时自动回退到 CPU，并记录警告日志。

#### Scenario: macOS 上无 GPU
- **WHEN** 用户在 macOS 上运行 OCR 功能
- **THEN** 系统自动使用 CPU 模式，不尝试使用 GPU

#### Scenario: GPU 不可用
- **WHEN** 配置了 `OCR_USE_GPU=True` 但系统无可用 GPU
- **THEN** 系统自动回退到 CPU，并记录警告日志

### Requirement: PaddleOCR 初始化异常捕获

系统 SHALL 捕获 PaddleOCR 初始化过程中的所有异常，记录详细错误信息，并向上层抛出明确的错误消息。

#### Scenario: PaddleOCR 初始化失败
- **WHEN** PaddleOCR 初始化失败（如依赖缺失、内存不足）
- **THEN** 系统记录完整的错误堆栈，并抛出包含用户友好提示的异常

## MODIFIED Requirements

### Requirement: OCR GPU 配置默认值

原配置：
```python
OCR_USE_GPU = os.environ.get('OCR_USE_GPU', 'true').lower() == 'true'
```

修改为：
```python
import platform
# macOS 上默认使用 CPU，其他平台默认使用 GPU
_default_use_gpu = 'false' if platform.system() == 'Darwin' else 'true'
OCR_USE_GPU = os.environ.get('OCR_USE_GPU', _default_use_gpu).lower() == 'true'
```

## REMOVED Requirements

无
