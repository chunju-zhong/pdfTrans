# 优化 PaddlePaddle OMP_NUM_THREADS 警告 Spec

## Why
OCR 子进程启动时 PaddlePaddle 输出 `OMP_NUM_THREADS set to 3, not 1` 警告，当前配置 `OMP_NUM_THREADS=2` 不符合 PaddlePaddle 数据并行模式的建议。

## What Changes
- 调整 `OMP_NUM_THREADS` 配置消除警告，同时保持 OCR 性能

## Impact
- Affected code: `modules/ocr/ocr_worker.py`
- Affected specs: 无

## ADDED Requirements

### Requirement: 优化线程数配置
系统 SHALL 配置 `OMP_NUM_THREADS=1` 以满足 PaddlePaddle 数据并行模式要求，同时通过 `MKL_NUM_THREADS` 控制底层 BLAS 并行度保持性能。

#### Scenario: 单页 OCR 性能不降低
- **WHEN** OCR 子进程处理单页 PDF
- **THEN** `OMP_NUM_THREADS=1`（满足 PaddlePaddle 数据并行模式要求）
- **AND** `MKL_NUM_THREADS` 设置为 CPU 核心数（控制底层 BLAS 并行度）
- **AND** 单页 OCR 速度不低于之前的配置

## MODIFIED Requirements

### Requirement: ocr_worker.py 环境变量配置
修改 `OMP_NUM_THREADS` 从 `thread_params.get('OMP_NUM_THREADS', '2')` 改为固定值 `'1'`。

修改前：
```python
os.environ['OMP_NUM_THREADS'] = thread_params.get('OMP_NUM_THREADS', '2')
```

修改后：
```python
os.environ['OMP_NUM_THREADS'] = '1'
```

## REMOVED Requirements

无
