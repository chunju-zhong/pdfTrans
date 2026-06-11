# Intel Mac 16GB OCR 深度内存优化 Spec

## Overview
- **Summary**: 针对 2.6 GHz 6-Core Intel Core i7 + Intel UHD Graphics 630 + 16GB RAM 这一特定硬件配置，深度优化 PaddleOCR 内存使用模式，强制纯 CPU 无 GPU/矢量加速干预，降低内存阈值和图像分辨率，确保进程不发生 SIGSEGV (exitcode=-11)
- **Purpose**: 当前分步加载+spawn上下文在该特定硬件上仍段错误，必须采取更极端的内存优化
- **Target Users**: Intel Mac 16GB 用户，非 M 系列芯片

## Goals
- OCR 子进程内存 RSS 峰值控制在 1.8GB 以内
- 不再出现 exitcode=-11 段错误
- 维持可接受的 OCR 识别精度

## Non-Goals (Out of Scope)
- 不更换 OCR 引擎（仍使用 PaddleOCR PP-StructureV3）
- 不放弃表格/公式识别功能（保留可配置开关）
- 不修改核心识别流程架构

## Background & Context
硬件配置细节：
- **CPU**: Intel Core i7-9750H 或同等，6核12线程
- **GPU**: Intel UHD Graphics 630，**仅 1.5GB VRAM**，无 NVIDIA CUDA
- **RAM**: 16GB DDR4，macOS 对单 Python 进程默认软限制 ~4GB
- **崩溃时刻**: 大概率在创建第一条管线 `pipeline.predict()` 首次执行时

推测的深层原因：
1. PaddlePaddle 即使 `device=cpu`，在 Intel 芯片上仍默认尝试使用 MKL-DNN / OneDNN 矢量加速
2. Intel UHD 集成显卡与主存共享显存，Paddle 可能误判可用 GPU 内存
3. 当前 2GB 内存阈值检查未计入 Paddle C++ 层池化分配的额外 "隐形" 内存

## Functional Requirements
- **FR-1**: 新增 OCR 引擎级别的纯 CPU 环境变量强制设置
- **FR-2**: 降低内存预检阈值，从 2GB 降至更保守值
- **FR-3**: 用户可配置跳过表格/公式识别，进一步减少内存
- **FR-4**: 页面粒度管线销毁与 GC，而非整批处理完再销毁
- **FR-5**: 进一步降低渲染 DPI 选项（120 DPI 甚至 96 DPI）

## Non-Functional Requirements
- **NFR-1**: OCR RSS 内存 ≤1.8GB（步骤1峰值）
- **NFR-2**: OCR 子进程 exitcode 永远是 0（成功）或非 -11 的其他错误码
- **NFR-3**: 120 DPI 模式下纯文本提取精度损失用户可接受

## Constraints
- **Technical**: 仍使用 PaddleOCR PP-StructureV3；不能假设用户有 NVIDIA CUDA；必须在 Intel UHD + 16GB 上稳定运行
- **Dependencies**: paddleocr, paddlepaddle 版本不变
- **Business**: 默认参数保持平衡；重度优化开关可通过 config/env var 开启

## Assumptions
- Intel Mac 16GB 是主要的受限环境，M 系列 16GB 不出现该问题
- 强制纯 CPU MKL/DNN 环境变量可让 Paddle 放弃任何类型的 GPU/矢量加速尝试
- 内存预检阈值设为可用内存的 60% 而不是固定 2GB，更适应不同场景

## Acceptance Criteria

### AC-1: MKL/DNN 纯 CPU 环境变量
- **Given**: OCR 子进程在 Intel Mac 上启动
- **When**: `_ocr_worker_func()` 执行
- **Then**: 设置 `OMP_NUM_THREADS=2`, `MKL_NUM_THREADS=2`, `DNNL_VERBOSE=0`, `CUDA_VISIBLE_DEVICES=-1`, `PADDLE_WITH_GPU=OFF`
- **Verification**: `programmatic`
- **Notes**: 环境变量在导入 paddle 前设置

### AC-2: 动态内存预检阈值
- **Given**: 16GB 系统，后台占用后约 8GB 可用
- **When**: `_create_pipeline()` 调用 `_check_available_memory()`
- **Then**: 内存阈值应为动态 `min(available * 0.55, 1.6GB)`，而非固定 2GB
- **Verification**: `programmatic`

### AC-3: 可配置跳过表格公式识别
- **Given**: 用户内存极度受限或不需要结构化数据
- **When**: `OCR_SKIP_TABLE=True`, `OCR_SKIP_FORMULA=True`
- **Then**: 只运行步骤1版面分析+文本OCR，跳过步骤2和3
- **Verification**: `programmatic`

### AC-4: 页面粒度管线销毁与 GC
- **Given**: 处理 N 个页面
- **When**: 每处理完 K 页后（如每5页或每10页）
- **Then**: `del pipeline`, `gc.collect()`, 然后 `_create_pipeline()` 重建管线继续
- **Verification**: `programmatic`

### AC-5: 更低的渲染 DPI 选项
- **Given**: OCR_AGGRESSIVE_OPT=True 或内存小于某个阈值
- **When**: 渲染 PDF 页面
- **Then**: 使用 120 DPI 替代默认 150 DPI，进一步降低图像内存和模型峰值
- **Verification**: `programmatic`

## Open Questions
- [ ] 是否默认启用内存激进优化，还是默认保守只让 opt-in？
- [ ] 120 DPI 模式下精度下降幅度是否需要评估？
- [ ] 步骤2/3能否做成单页面处理+立即销毁，而非目前全部页面批量处理？
