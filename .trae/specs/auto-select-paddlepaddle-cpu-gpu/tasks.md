# Tasks

- [x] Task 1: 修改 requirements.txt，将 PaddlePaddle 包注释掉并添加说明
  - [x] SubTask 1.1: 将 `paddlepaddle>=3.0.0` 和 `paddlepaddle-gpu>=3.0.0` 都注释掉，添加说明指向 `install_paddle.sh`

- [x] Task 2: 创建 install_paddle.sh 安装脚本
  - [x] SubTask 2.1: 检测 OS（macOS → CPU）
  - [x] SubTask 2.2: 检测 nvidia-smi 是否可用
  - [x] SubTask 2.3: 检测 CUDA 版本
  - [x] SubTask 2.4: 根据检测结果安装对应的 paddlepaddle 或 paddlepaddle-gpu

- [x] Task 3: 更新 README.md（英文版）
  - [x] SubTask 3.1: 移除"不支持OCR"的说明，添加 OCR 功能说明
  - [x] SubTask 3.2: 更新安装步骤，添加 install_paddle.sh 和 OCR 依赖安装说明
  - [x] SubTask 3.3: 更新 Web 使用说明，添加 OCR 模式选项说明
  - [x] SubTask 3.4: 更新 CLI 使用说明，添加 --ocr、--ocr-engine、--ocr-lang 选项
  - [x] SubTask 3.5: 添加 GPU 加速说明（OCR_USE_GPU 环境变量）

- [x] Task 4: 更新 README.zh.md（中文版）
  - [x] SubTask 4.1: 移除"不支持OCR"的说明，添加 OCR 功能说明
  - [x] SubTask 4.2: 更新安装步骤，添加 install_paddle.sh 和 OCR 依赖安装说明
  - [x] SubTask 4.3: 更新 Web 使用说明，添加 OCR 模式选项说明
  - [x] SubTask 4.4: 更新 CLI 使用说明，添加 --ocr、--ocr-engine、--ocr-lang 选项
  - [x] SubTask 4.5: 添加 GPU 加速说明（OCR_USE_GPU 环境变量）

# Task Dependencies

- [Task 2] 独立
- [Task 1] 独立
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 3] 和 [Task 4] 可并行
