#!/bin/bash
# PaddlePaddle 自动安装脚本
# 根据硬件环境自动选择安装 CPU 或 GPU 版本
# 用法: bash install_paddle.sh

set -e

echo "=== PaddlePaddle 安装脚本 ==="
echo ""

# 检测操作系统
OS="$(uname -s)"
echo "检测到操作系统: $OS"

# macOS 不支持 GPU 版本
if [ "$OS" = "Darwin" ]; then
    echo "macOS 环境，安装 CPU 版本..."
    pip install "paddlepaddle>=3.0.0"
    echo "✓ PaddlePaddle CPU 版本安装完成"
    exit 0
fi

# 检测 NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "未检测到 nvidia-smi，无 NVIDIA GPU，安装 CPU 版本..."
    pip install "paddlepaddle>=3.0.0"
    echo "✓ PaddlePaddle CPU 版本安装完成"
    exit 0
fi

# 检测 CUDA 版本
echo "检测到 NVIDIA GPU"
CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
if [ -z "$CUDA_VERSION" ]; then
    echo "无法检测 CUDA 版本，安装 CPU 版本..."
    pip install "paddlepaddle>=3.0.0"
    echo "✓ PaddlePaddle CPU 版本安装完成"
    exit 0
fi

echo "检测到 CUDA 版本: $CUDA_VERSION"

# 根据CUDA版本安装
CUDA_MAJOR=$(echo "$CUDA_VERSION" | cut -d. -f1)
CUDA_MINOR=$(echo "$CUDA_VERSION" | cut -d. -f2)

if [ "$CUDA_MAJOR" -ge 12 ] 2>/dev/null; then
    echo "CUDA >= 12.0，安装 GPU 版本..."
    pip install "paddlepaddle-gpu>=3.0.0"
    echo "✓ PaddlePaddle GPU 版本安装完成"
elif [ "$CUDA_MAJOR" -eq 11 ] && [ "$CUDA_MINOR" -ge 8 ] 2>/dev/null; then
    echo "CUDA 11.8+，安装 GPU 版本..."
    pip install "paddlepaddle-gpu>=3.0.0"
    echo "✓ PaddlePaddle GPU 版本安装完成"
else
    echo "CUDA 版本较低 ($CUDA_VERSION)，安装 CPU 版本..."
    pip install "paddlepaddle>=3.0.0"
    echo "✓ PaddlePaddle CPU 版本安装完成"
fi

echo ""
echo "安装完成！可以通过以下命令验证："
echo "  python -c 'import paddle; print(paddle.__version__)'"
