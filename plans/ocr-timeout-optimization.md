# OCR 超时处理优化蓝图

> 目标：解决 OCR 子进程超时误判、参数硬编码、无重试机制三大问题

## 问题分析

### 当前架构

```
TranslationService.process_translation()
  └── PdfExtractor.extract() [ocr_mode=True]
        └── run_ocr_in_subprocess(timeout=600)
              └── _ocr_worker_func() [spawn 子进程]
                    └── PaddleOcrExtractor.extract_from_pdf()
```

### 三大核心问题

| # | 问题 | 根因 | 影响 |
|---|------|------|------|
| P1 | 超时=死机误判 | 父进程仅用 `process.join(timeout)` 判断，无法区分"正在工作但慢"和"已死机" | 大PDF正常处理被误杀，用户被迫等待600秒才发现死机 |
| P2 | 参数硬编码 | `CPU_NUM=2`, `OMP_NUM_THREADS=2`, `MEMORY_FACTOR=0.55` 等全部硬编码 | 4核机器只用2核，16GB机器与8GB机器用相同阈值 |
| P3 | 无重试机制 | 子进程崩溃/超时后直接抛 RuntimeError | 临时性内存不足或偶发段错误导致整个翻译任务失败 |

---

## 步骤总览

| 步骤 | 名称 | 依赖 | 涉及文件 | 模型级别 |
|------|------|------|----------|----------|
| 1 | 心跳状态报告机制 | 无 | `modules/ocr/ocr_worker.py` | default |
| 2 | 父进程智能超时监控 | 步骤1 | `modules/ocr/ocr_worker.py` | default |
| 3 | 系统负载感知模块 | 无 | `modules/ocr/system_profiler.py`(新), `config.py` | default |
| 4 | 动态参数调整集成 | 步骤3 | `modules/ocr/ocr_worker.py`, `modules/ocr/paddle_extractor.py` | default |
| 5 | 重试机制 | 步骤2, 步骤4 | `modules/ocr/ocr_worker.py`, `modules/pdf_extractor.py` | default |
| 6 | 配置扩展与测试 | 步骤5 | `config.py`, `tests/test_ocr_worker.py`(新) | default |

### 依赖图

```
步骤1(心跳) ──→ 步骤2(智能监控) ──┐
                                    ├──→ 步骤5(重试机制) ──→ 步骤6(配置+测试)
步骤3(负载感知) ──→ 步骤4(动态参数) ──┘
```

**可并行**：步骤1+步骤3 可同时执行；步骤2+步骤4 可同时执行

---

## 步骤 1: 心跳状态报告机制

### 目标

子进程定期向父进程报告当前状态（正在处理哪一页、哪个步骤、内存使用量），使父进程能区分"正在工作"和"已死机"。

### 上下文简报

**当前代码**：[ocr_worker.py](file:///Users/chunju/work/pdfTrans/modules/ocr/ocr_worker.py) 的 `_ocr_worker_func` 通过 `result_queue` 仅在完成时发送一次 `('success', data)` 或 `('error', msg)`。父进程在 600 秒内收不到任何消息就判定超时。

**关键约束**：
- 使用 `multiprocessing.get_context('spawn')` 创建子进程，spawn 模式下子进程不继承父进程内存
- `result_queue` 是 `ctx.Queue()` 实例，支持 `put()` / `get()` 非阻塞操作
- PaddleOCR 的 `pipeline.predict()` 是同步阻塞调用，单页处理可能耗时 30-120 秒

### 实现方案

#### 1.1 定义状态消息协议

在 `ocr_worker.py` 顶部定义状态消息类型：

```python
STATUS_HEARTBEAT = 'heartbeat'
STATUS_STEP_START = 'step_start'
STATUS_STEP_PROGRESS = 'step_progress'
STATUS_STEP_COMPLETE = 'step_complete'
STATUS_RESULT = 'result'
STATUS_ERROR = 'error'
```

每条状态消息格式：`(type: str, payload: dict)`

- `heartbeat`: `{'pid': int, 'memory_mb': float, 'timestamp': float}`
- `step_start`: `{'step': int, 'step_name': str, 'total_pages': int}`
- `step_progress`: `{'step': int, 'page_num': int, 'pages_done': int, 'total_pages': int}`
- `step_complete`: `{'step': int, 'step_name': str, 'duration_sec': float}`
- `result`: `('success', result_dict)` — 保持向后兼容
- `error`: `('error', error_message)` — 保持向后兼容

#### 1.2 心跳线程

在 `_ocr_worker_func` 中启动一个守护线程，每 15 秒向 `status_queue` 发送心跳：

```python
import threading
import time

def _heartbeat_sender(status_queue, stop_event):
    while not stop_event.is_set():
        try:
            mem_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            status_queue.put((STATUS_HEARTBEAT, {
                'pid': os.getpid(),
                'memory_mb': mem_mb,
                'timestamp': time.time(),
            }))
        except Exception:
            pass
        stop_event.wait(15)
```

#### 1.3 修改 `_ocr_worker_func` 签名

新增 `status_queue` 参数：

```python
def _ocr_worker_func(pdf_path, pages, temp_images_dir, lang, use_gpu,
                     result_queue, status_queue):
```

在函数入口启动心跳线程，在退出时停止：

```python
stop_event = threading.Event()
heartbeat_thread = threading.Thread(
    target=_heartbeat_sender,
    args=(status_queue, stop_event),
    daemon=True,
)
heartbeat_thread.start()

try:
    # ... existing OCR logic ...
    # 在每个步骤和每页处理时发送状态
    status_queue.put((STATUS_STEP_START, {'step': 1, 'step_name': '版面分析+文本OCR', 'total_pages': len(target_pages)}))
    # ... per-page processing ...
    status_queue.put((STATUS_STEP_PROGRESS, {'step': 1, 'page_num': page_num, 'pages_done': done, 'total_pages': total}))
    # ... after all steps ...
    result_queue.put(('success', result.to_dict()))
finally:
    stop_event.set()
    heartbeat_thread.join(timeout=3)
```

#### 1.4 修改 PaddleOcrExtractor 接受状态回调

在 `PaddleOcrExtractor.extract_from_pdf()` 中添加可选的 `status_callback` 参数：

```python
def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None, status_callback=None):
```

在每个步骤和每页处理完成时调用：

```python
if status_callback:
    status_callback(STATUS_STEP_PROGRESS, {...})
```

### 验证命令

```bash
cd /Users/chunju/work/pdfTrans && python -c "
from modules.ocr.ocr_worker import run_ocr_in_subprocess
import time
# 使用一个小的测试PDF验证心跳消息
"
```

### 退出标准

- [ ] 子进程每 15 秒发送心跳消息
- [ ] 每页处理完成时发送进度消息
- [ ] 每个步骤开始/完成时发送状态消息
- [ ] 心跳线程在子进程退出时正确停止

---

## 步骤 2: 父进程智能超时监控

### 目标

父进程不再简单以固定超时判断子进程死机，而是基于心跳活跃度判断：如果子进程持续发送心跳，说明仍在工作，不终止；如果心跳中断超过阈值，才判定死机。

### 上下文简报

**当前代码**：[ocr_worker.py:118-127](file:///Users/chunju/work/pdfTrans/modules/ocr/ocr_worker.py#L118-L127) 使用 `process.join(timeout=600)` 阻塞等待，超时后直接 `terminate()` + `kill()`。

**关键约束**：
- `status_queue` 是 `multiprocessing.Queue`，支持 `get(timeout=...)` 非阻塞读取
- 需要同时监听 `status_queue`（心跳）和 `result_queue`（最终结果）
- 不能使用 `select()` 因为 Queue 不是文件描述符

### 实现方案

#### 2.1 替换 `process.join()` 为轮询监控循环

```python
def run_ocr_in_subprocess(pdf_path, pages=None, temp_images_dir=None,
                          lang='ch', use_gpu=False, timeout=600,
                          heartbeat_timeout=90, max_total_time=1800):
```

参数说明：
- `timeout`: 单步无心跳超时（秒），默认 90 秒 — 心跳中断超过此时间判定死机
- `max_total_time`: 总最大执行时间（秒），默认 1800 秒 — 防止无限运行
- `heartbeat_timeout`: 向后兼容的别名

核心监控循环：

```python
process.start()
start_time = time.time()
last_heartbeat_time = time.time()
last_progress = None

while True:
    # 检查总超时
    elapsed = time.time() - start_time
    if elapsed > max_total_time:
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join()
        raise RuntimeError(f"OCR处理超过最大时间（{max_total_time}秒），已终止子进程")

    # 检查子进程是否已退出
    if not process.is_alive():
        break

    # 非阻塞读取状态队列
    try:
        msg_type, payload = status_queue.get(timeout=5)
        if msg_type == STATUS_HEARTBEAT:
            last_heartbeat_time = time.time()
            logger.debug(f"OCR子进程心跳: pid={payload.get('pid')}, "
                        f"内存={payload.get('memory_mb', 0):.0f}MB")
        elif msg_type == STATUS_STEP_START:
            last_heartbeat_time = time.time()
            logger.info(f"OCR步骤{payload['step']}开始: {payload['step_name']}")
        elif msg_type == STATUS_STEP_PROGRESS:
            last_heartbeat_time = time.time()
            last_progress = payload
            logger.info(f"OCR步骤{payload['step']}进度: "
                       f"{payload['pages_done']}/{payload['total_pages']}页, "
                       f"当前第{payload['page_num']}页")
        elif msg_type == STATUS_STEP_COMPLETE:
            last_heartbeat_time = time.time()
            logger.info(f"OCR步骤{payload['step']}完成: "
                       f"{payload['step_name']}, 耗时{payload['duration_sec']:.1f}秒")
    except queue.Empty:
        pass  # 5秒内无消息，继续循环

    # 检查心跳超时
    heartbeat_silence = time.time() - last_heartbeat_time
    if heartbeat_silence > heartbeat_timeout:
        logger.error(
            f"OCR子进程心跳中断{heartbeat_silence:.0f}秒 "
            f"(超过阈值{heartbeat_timeout}秒)，判定子进程死机。"
            f"最后进度: {last_progress}"
        )
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join()
        raise RuntimeError(
            f"OCR子进程心跳中断{heartbeat_silence:.0f}秒，判定死机已终止。"
            f"最后进度: {last_progress}"
        )

# 子进程已退出，读取结果
if process.exitcode != 0:
    raise RuntimeError(...)

try:
    status, data = result_queue.get(timeout=10)
except queue.Empty:
    raise RuntimeError("OCR子进程未返回结果，可能已崩溃")
```

#### 2.2 区分三种失败场景

| 场景 | 判定条件 | 错误消息 | 重试策略 |
|------|----------|----------|----------|
| 心跳中断（死机） | 心跳沉默 > `heartbeat_timeout` | "OCR子进程心跳中断X秒，判定死机" | 可重试（降低参数） |
| 总时间超限 | 运行时间 > `max_total_time` | "OCR处理超过最大时间" | 可重试（降低参数） |
| 异常退出 | `exitcode != 0` | "OCR子进程异常退出" | 可重试（降低参数） |

### 验证命令

```bash
cd /Users/chunju/work/pdfTrans && python -m pytest tests/test_ocr_worker.py -v -k "test_heartbeat"
```

### 退出标准

- [ ] 父进程不再使用 `process.join(timeout)` 阻塞等待
- [ ] 心跳活跃时不终止子进程，即使超过原 600 秒
- [ ] 心跳中断超过 `heartbeat_timeout` 才判定死机
- [ ] 总执行时间超过 `max_total_time` 时强制终止
- [ ] 日志中记录子进程的步骤和页面进度

---

## 步骤 3: 系统负载感知模块

### 目标

创建独立的系统负载探测模块，根据 CPU 核数、可用内存、GPU 状态动态计算 OCR 参数，替代所有硬编码值。

### 上下文简报

**当前硬编码值**：
- [ocr_worker.py:29-41](file:///Users/chunju/work/pdfTrans/modules/ocr/ocr_worker.py#L29-L41): `CPU_NUM=2`, `OMP_NUM_THREADS=2`, `MKL_NUM_THREADS=2`, `OPENBLAS_NUM_THREADS=2`
- [paddle_extractor.py:89-92](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L89-L92): `MEMORY_FACTOR=0.55`, `MEMORY_CAP_LAYOUT=1600MB`, `MEMORY_CAP_TABLE=1600MB`, `MEMORY_CAP_FORMULA=1000MB`
- [ocr_worker.py:92](file:///Users/chunju/work/pdfTrans/modules/ocr/ocr_worker.py#L92): `timeout=600`

**关键约束**：
- `psutil` 已在 `requirements.txt` 中
- 参数需要在子进程启动前计算，通过参数传递给子进程
- 不同机器配置差异大：2核4GB vs 16核64GB vs GPU服务器

### 实现方案

#### 3.1 创建 `modules/ocr/system_profiler.py`

```python
import os
import logging
import psutil

logger = logging.getLogger(__name__)


class SystemProfile:
    def __init__(self):
        self.cpu_count = psutil.cpu_count(logical=False) or 2
        self.cpu_count_logical = psutil.cpu_count(logical=True) or 2
        self.total_memory_gb = psutil.virtual_memory().total / (1024 ** 3)
        self.available_memory_gb = psutil.virtual_memory().available / (1024 ** 3)
        self.memory_percent = psutil.virtual_memory().percent
        self.gpu_available = self._detect_gpu()
        self.gpu_count = self._count_gpus()
        self.load_avg_1m = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0

    def _detect_gpu(self):
        try:
            import paddle
            return paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0
        except Exception:
            return False

    def _count_gpus(self):
        try:
            import paddle
            return paddle.device.cuda.device_count() if self.gpu_available else 0
        except Exception:
            return 0

    def is_high_load(self):
        return self.memory_percent > 85 or self.load_avg_1m > self.cpu_count * 0.8

    def is_low_memory(self):
        return self.available_memory_gb < 4.0


class OcrParameterCalculator:
    MEMORY_TIERS = {
        'minimal': (0, 8),
        'low': (8, 16),
        'medium': (16, 32),
        'high': (32, 64),
        'unlimited': (64, float('inf')),
    }

    def __init__(self, profile: SystemProfile):
        self.profile = profile

    def _memory_tier(self):
        avail = self.profile.available_memory_gb
        for tier, (lo, hi) in self.MEMORY_TIERS.items():
            if lo <= avail < hi:
                return tier
        return 'minimal'

    def compute_thread_params(self):
        tier = self._memory_tier()
        cpu = self.profile.cpu_count
        avail_gb = self.profile.available_memory_gb

        if self.profile.is_high_load():
            compute_threads = max(1, cpu // 4)
        elif tier == 'minimal':
            compute_threads = max(1, min(2, cpu))
        elif tier == 'low':
            compute_threads = max(2, min(cpu, 4))
        elif tier == 'medium':
            compute_threads = max(2, min(cpu, 6))
        else:
            compute_threads = max(2, min(cpu, 8))

        return {
            'CPU_NUM': str(compute_threads),
            'OMP_NUM_THREADS': str(compute_threads),
            'MKL_NUM_THREADS': str(compute_threads),
            'OPENBLAS_NUM_THREADS': str(compute_threads),
        }

    def compute_memory_params(self):
        tier = self._memory_tier()
        avail = self.profile.available_memory_gb

        if tier == 'minimal':
            factor = 0.35
            cap_layout = 800
            cap_table = 800
            cap_formula = 500
        elif tier == 'low':
            factor = 0.45
            cap_layout = 1200
            cap_table = 1200
            cap_formula = 800
        elif tier == 'medium':
            factor = 0.55
            cap_layout = 1600
            cap_table = 1600
            cap_formula = 1000
        else:
            factor = 0.60
            cap_layout = 2400
            cap_table = 2400
            cap_formula = 1500

        if self.profile.is_high_load():
            factor *= 0.7
            cap_layout = int(cap_layout * 0.7)
            cap_table = int(cap_table * 0.7)
            cap_formula = int(cap_formula * 0.7)

        return {
            'memory_factor': factor,
            'memory_cap_layout': cap_layout * 1024 * 1024,
            'memory_cap_table': cap_table * 1024 * 1024,
            'memory_cap_formula': cap_formula * 1024 * 1024,
        }

    def compute_render_dpi(self, user_dpi=None):
        tier = self._memory_tier()
        if user_dpi:
            return user_dpi
        if tier in ('minimal', 'low'):
            return 100
        elif tier == 'medium':
            return 120
        else:
            return 150

    def compute_timeout_params(self, page_count=1):
        tier = self._memory_tier()
        base_per_page = {
            'minimal': 120,
            'low': 90,
            'medium': 60,
            'high': 45,
            'unlimited': 30,
        }.get(tier, 90)

        if self.profile.is_high_load():
            base_per_page = int(base_per_page * 1.5)

        heartbeat_timeout = max(90, base_per_page * 2)
        max_total_time = max(600, base_per_page * page_count * 2 + 300)

        return {
            'heartbeat_timeout': heartbeat_timeout,
            'max_total_time': min(max_total_time, 3600),
        }

    def should_skip_table(self):
        tier = self._memory_tier()
        return tier == 'minimal' and self.profile.available_memory_gb < 6

    def should_skip_formula(self):
        tier = self._memory_tier()
        return tier == 'minimal'

    def compute_all_params(self, page_count=1, user_dpi=None):
        return {
            'thread_params': self.compute_thread_params(),
            'memory_params': self.compute_memory_params(),
            'render_dpi': self.compute_render_dpi(user_dpi),
            'timeout_params': self.compute_timeout_params(page_count),
            'skip_table': self.should_skip_table(),
            'skip_formula': self.should_skip_formula(),
            'use_gpu': self.profile.gpu_available and not self.profile.is_high_load(),
        }


def get_ocr_params(page_count=1, user_dpi=None):
    profile = SystemProfile()
    calculator = OcrParameterCalculator(profile)
    params = calculator.compute_all_params(page_count, user_dpi)
    logger.info(
        f"系统负载感知参数: CPU={profile.cpu_count}核, "
        f"可用内存={profile.available_memory_gb:.1f}GB, "
        f"GPU={profile.gpu_available}, 高负载={profile.is_high_load()}, "
        f"内存层级={calculator._memory_tier()}, "
        f"线程数={params['thread_params']['CPU_NUM']}, "
        f"内存因子={params['memory_params']['memory_factor']:.2f}, "
        f"DPI={params['render_dpi']}, "
        f"心跳超时={params['timeout_params']['heartbeat_timeout']}s, "
        f"最大时间={params['timeout_params']['max_total_time']}s"
    )
    return params
```

#### 3.2 在 `config.py` 中添加新配置项

```python
OCR_HEARTBEAT_TIMEOUT = int(os.environ.get('OCR_HEARTBEAT_TIMEOUT', '90'))
OCR_MAX_TOTAL_TIME = int(os.environ.get('OCR_MAX_TOTAL_TIME', '1800'))
OCR_MAX_RETRIES = int(os.environ.get('OCR_MAX_RETRIES', '2'))
OCR_RETRY_BACKOFF = float(os.environ.get('OCR_RETRY_BACKOFF', '5.0'))
OCR_DYNAMIC_PARAMS = os.environ.get('OCR_DYNAMIC_PARAMS', 'true').lower() == 'true'
```

### 验证命令

```bash
cd /Users/chunju/work/pdfTrans && python -c "
from modules.ocr.system_profiler import get_ocr_params
params = get_ocr_params(page_count=10)
import json
print(json.dumps(params, indent=2, default=str))
"
```

### 退出标准

- [ ] `SystemProfile` 正确检测 CPU 核数、内存、GPU
- [ ] `OcrParameterCalculator` 根据内存层级输出不同参数
- [ ] 高负载时自动降低线程数和内存阈值
- [ ] 所有参数可通过环境变量覆盖

---

## 步骤 4: 动态参数调整集成

### 目标

将 `system_profiler` 的动态参数集成到 `ocr_worker.py` 和 `paddle_extractor.py`，替换所有硬编码值。

### 上下文简报

**需要替换的硬编码值**：
1. [ocr_worker.py:28-41](file:///Users/chunju/work/pdfTrans/modules/ocr/ocr_worker.py#L28-L41) — 环境变量硬编码
2. [paddle_extractor.py:89-92](file:///Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py#L89-L92) — 内存阈值类常量
3. [ocr_worker.py:92](file:///Users/chunju/work/pdfTrans/modules/ocr/ocr_worker.py#L92) — `timeout=600` 默认参数

### 实现方案

#### 4.1 修改 `run_ocr_in_subprocess` 签名

```python
def run_ocr_in_subprocess(pdf_path, pages=None, temp_images_dir=None,
                          lang='ch', use_gpu=False, timeout=None,
                          heartbeat_timeout=None, max_total_time=None,
                          ocr_params=None):
```

- `ocr_params`: 由 `get_ocr_params()` 返回的完整参数字典
- 当 `ocr_params=None` 且 `config.OCR_DYNAMIC_PARAMS=True` 时自动计算
- 当 `ocr_params=None` 且 `config.OCR_DYNAMIC_PARAMS=False` 时使用旧默认值

#### 4.2 在子进程启动前计算参数

```python
from modules.ocr.system_profiler import get_ocr_params

if ocr_params is None and config.OCR_DYNAMIC_PARAMS:
    page_count = len(pages) if pages else _estimate_page_count(pdf_path)
    ocr_params = get_ocr_params(page_count=page_count)

thread_params = ocr_params.get('thread_params', {}) if ocr_params else {}
memory_params = ocr_params.get('memory_params', {}) if ocr_params else {}
timeout_params = ocr_params.get('timeout_params', {}) if ocr_params else {}
```

#### 4.3 传递动态环境变量给子进程

修改 `_ocr_worker_func` 接受 `ocr_params` 参数：

```python
def _ocr_worker_func(pdf_path, pages, temp_images_dir, lang, use_gpu,
                     result_queue, status_queue, ocr_params):
    import os
    thread_params = ocr_params.get('thread_params', {}) if ocr_params else {}
    os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0.5'
    os.environ['CPU_NUM'] = thread_params.get('CPU_NUM', '2')
    os.environ['OMP_NUM_THREADS'] = thread_params.get('OMP_NUM_THREADS', '2')
    os.environ['MKL_NUM_THREADS'] = thread_params.get('MKL_NUM_THREADS', '2')
    os.environ['OPENBLAS_NUM_THREADS'] = thread_params.get('OPENBLAS_NUM_THREADS', '2')
    # ... rest of env vars remain the same ...
```

#### 4.4 修改 PaddleOcrExtractor 使用动态内存参数

将类常量改为实例属性，接受外部参数：

```python
class PaddleOcrExtractor(OcrExtractor):
    def __init__(self, lang='ch', use_gpu=True, memory_params=None, skip_table=False, skip_formula=False):
        self.lang = lang
        self.use_gpu = use_gpu
        self._actual_device = None
        self._memory_factor = (memory_params or {}).get('memory_factor', 0.55)
        self._memory_cap_layout = (memory_params or {}).get('memory_cap_layout', 1600 * 1024 * 1024)
        self._memory_cap_table = (memory_params or {}).get('memory_cap_table', 1600 * 1024 * 1024)
        self._memory_cap_formula = (memory_params or {}).get('memory_cap_formula', 1000 * 1024 * 1024)
        self._skip_table = skip_table
        self._skip_formula = skip_formula
```

将 `_create_pipeline` 中的 `self.MEMORY_FACTOR` / `self.MEMORY_CAP_*` 替换为实例属性。

将 `extract_from_pdf` 中的 `config.OCR_SKIP_TABLE` / `config.OCR_SKIP_FORMULA` 替换为实例属性（优先）或配置值（回退）。

#### 4.5 传递 memory_params 到子进程

在 `_ocr_worker_func` 中：

```python
memory_params = ocr_params.get('memory_params', {}) if ocr_params else {}
skip_table = ocr_params.get('skip_table', config.OCR_SKIP_TABLE) if ocr_params else config.OCR_SKIP_TABLE
skip_formula = ocr_params.get('skip_formula', config.OCR_SKIP_FORMULA) if ocr_params else config.OCR_SKIP_FORMULA

extractor = PaddleOcrExtractor(
    lang=lang,
    use_gpu=use_gpu,
    memory_params=memory_params,
    skip_table=skip_table,
    skip_formula=skip_formula,
)
```

### 验证命令

```bash
cd /Users/chunju/work/pdfTrans && python -c "
from modules.ocr.ocr_worker import run_ocr_in_subprocess
from modules.ocr.system_profiler import get_ocr_params
params = get_ocr_params(page_count=5)
print('Dynamic params:', params)
"
```

### 退出标准

- [ ] `CPU_NUM` 等环境变量根据实际 CPU 核数动态设置
- [ ] 内存阈值根据可用内存动态计算
- [ ] `config.OCR_DYNAMIC_PARAMS=False` 时回退到旧硬编码值
- [ ] 所有现有测试通过

---

## 步骤 5: 重试机制

### 目标

子进程死机或异常退出后，自动重试。重试时根据失败原因动态降低参数（减少线程数、降低DPI、跳过表格/公式），提高重试成功率。

### 上下文简报

**当前行为**：[pdf_extractor.py:187-190](file:///Users/chunju/work/pdfTrans/modules/pdf_extractor.py#L187-L190) 调用 `run_ocr_in_subprocess()` 失败后直接抛异常，[translation_service.py:259](file:///Users/chunju/work/pdfTrans/services/translation_service.py#L259) 捕获后设置任务失败。

**关键约束**：
- 重试应在 `ocr_worker.py` 层面实现，对上层透明
- 每次重试应降低参数，避免相同原因再次失败
- 重试次数和间隔可配置
- 需要区分可重试错误（内存不足、段错误）和不可重试错误（文件不存在、参数错误）

### 实现方案

#### 5.1 定义可重试错误类型

```python
class OcrRetryableError(RuntimeError):
    """可重试的OCR错误（内存不足、段错误、心跳中断等）"""
    pass

class OcrFatalError(RuntimeError):
    """不可重试的OCR错误（文件不存在、参数错误等）"""
    pass
```

在 `run_ocr_in_subprocess` 中区分错误类型：
- 心跳中断 → `OcrRetryableError`
- 异常退出（exitcode != 0） → `OcrRetryableError`
- 总时间超限 → `OcrRetryableError`
- 结果解析失败 → `OcrRetryableError`
- 文件不存在 → `OcrFatalError`

#### 5.2 实现重试包装器

```python
def run_ocr_in_subprocess(pdf_path, pages=None, temp_images_dir=None,
                          lang='ch', use_gpu=False, timeout=None,
                          heartbeat_timeout=None, max_total_time=None,
                          ocr_params=None, max_retries=None, retry_backoff=None):
    if max_retries is None:
        max_retries = config.OCR_MAX_RETRIES
    if retry_backoff is None:
        retry_backoff = config.OCR_RETRY_BACKOFF

    last_error = None
    current_params = ocr_params

    for attempt in range(max_retries + 1):
        try:
            return _run_ocr_once(
                pdf_path, pages, temp_images_dir, lang, use_gpu,
                heartbeat_timeout, max_total_time, current_params
            )
        except OcrRetryableError as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    f"OCR第{attempt + 1}次尝试失败: {str(e)}，"
                    f"{retry_backoff}秒后重试（剩余{max_retries - attempt}次）"
                )
                time.sleep(retry_backoff)
                current_params = _degrade_params(current_params, attempt)
                retry_backoff *= 1.5
            else:
                logger.error(
                    f"OCR已重试{max_retries}次仍失败，最后错误: {str(e)}"
                )
        except OcrFatalError:
            raise

    raise last_error
```

#### 5.3 参数降级策略

```python
def _degrade_params(current_params, attempt):
    if current_params is None:
        from modules.ocr.system_profiler import get_ocr_params
        current_params = get_ocr_params(page_count=1)

    degraded = dict(current_params)

    thread_params = dict(degraded.get('thread_params', {}))
    for key in ('CPU_NUM', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
        current = int(thread_params.get(key, '2'))
        thread_params[key] = str(max(1, current - 1))
    degraded['thread_params'] = thread_params

    memory_params = dict(degraded.get('memory_params', {}))
    memory_params['memory_factor'] = memory_params.get('memory_factor', 0.55) * 0.8
    for cap_key in ('memory_cap_layout', 'memory_cap_table', 'memory_cap_formula'):
        if cap_key in memory_params:
            memory_params[cap_key] = int(memory_params[cap_key] * 0.8)
    degraded['memory_params'] = memory_params

    current_dpi = degraded.get('render_dpi', 120)
    degraded['render_dpi'] = max(72, current_dpi - 20)

    if attempt >= 1:
        degraded['skip_table'] = True
    if attempt >= 2:
        degraded['skip_formula'] = True

    logger.info(
        f"参数降级(第{attempt + 1}次重试): "
        f"线程={thread_params.get('CPU_NUM')}, "
        f"DPI={degraded['render_dpi']}, "
        f"跳过表格={degraded.get('skip_table')}, "
        f"跳过公式={degraded.get('skip_formula')}"
    )
    return degraded
```

#### 5.4 修改 `pdf_extractor.py` 调用

无需修改 — `run_ocr_in_subprocess` 的重试逻辑对上层透明，接口签名不变（新增参数均有默认值）。

### 验证命令

```bash
cd /Users/chunju/work/pdfTrans && python -m pytest tests/test_ocr_worker.py -v -k "test_retry"
```

### 退出标准

- [ ] 子进程死机后自动重试，最多 `OCR_MAX_RETRIES` 次
- [ ] 每次重试自动降低参数
- [ ] 第二次重试跳过表格，第三次重试跳过公式
- [ ] 不可重试错误直接抛出，不重试
- [ ] 重试日志清晰记录每次尝试的参数和结果

---

## 步骤 6: 配置扩展与测试

### 目标

扩展 `config.py` 中的 OCR 配置项，编写完整的单元测试覆盖所有新功能。

### 上下文简报

**当前测试**：项目有 `tests/` 目录，使用 pytest。需要检查是否有现有 OCR 相关测试。

### 实现方案

#### 6.1 config.py 新增配置项汇总

```python
OCR_HEARTBEAT_TIMEOUT = int(os.environ.get('OCR_HEARTBEAT_TIMEOUT', '90'))
OCR_MAX_TOTAL_TIME = int(os.environ.get('OCR_MAX_TOTAL_TIME', '1800'))
OCR_MAX_RETRIES = int(os.environ.get('OCR_MAX_RETRIES', '2'))
OCR_RETRY_BACKOFF = float(os.environ.get('OCR_RETRY_BACKOFF', '5.0'))
OCR_DYNAMIC_PARAMS = os.environ.get('OCR_DYNAMIC_PARAMS', 'true').lower() == 'true'
```

#### 6.2 测试文件 `tests/test_ocr_worker.py`

测试用例清单：

| 测试 | 描述 |
|------|------|
| `test_system_profile_detection` | SystemProfile 正确检测 CPU/内存/GPU |
| `test_parameter_calculator_minimal` | 极小内存（<8GB）输出保守参数 |
| `test_parameter_calculator_high` | 大内存（>32GB）输出激进参数 |
| `test_parameter_calculator_high_load` | 高负载时自动降低参数 |
| `test_parameter_degradation` | 重试时参数逐级降级 |
| `test_heartbeat_timeout_detection` | 心跳中断时判定死机 |
| `test_heartbeat_active_no_kill` | 心跳活跃时不终止子进程 |
| `test_retry_on_crash` | 子进程崩溃后自动重试 |
| `test_retry_with_degraded_params` | 重试时使用降级参数 |
| `test_fatal_error_no_retry` | 不可重试错误直接抛出 |
| `test_max_retries_exhausted` | 重试次数用尽后抛出最后错误 |
| `test_dynamic_params_disabled` | OCR_DYNAMIC_PARAMS=False 时使用旧默认值 |

#### 6.3 Mock 策略

- `psutil` 相关调用：Mock 返回不同配置（2核4GB / 8核16GB / 16核64GB）
- 子进程：Mock `multiprocessing.Process` 模拟不同退出场景
- PaddleOCR：Mock `PPStructureV3` 避免实际加载模型

### 验证命令

```bash
cd /Users/chunju/work/pdfTrans && python -m pytest tests/test_ocr_worker.py -v --tb=short
```

### 退出标准

- [ ] 所有新配置项可通过环境变量设置
- [ ] 所有测试用例通过
- [ ] 测试覆盖率 ≥ 80%
- [ ] 现有测试不受影响

---

## 回滚策略

| 步骤 | 回滚方式 |
|------|----------|
| 1 | 移除 `status_queue` 参数，恢复原 `_ocr_worker_func` 签名 |
| 2 | 恢复 `process.join(timeout)` 逻辑 |
| 3 | 删除 `system_profiler.py` |
| 4 | 恢复硬编码环境变量和类常量 |
| 5 | 移除重试包装器，`run_ocr_in_subprocess` 直接调用 |
| 6 | 移除新配置项和测试文件 |

每个步骤独立可回滚，不影响其他步骤。

---

## 不变量（所有步骤完成后必须成立）

1. **向后兼容**：所有新参数有默认值，不传参时行为与当前一致
2. **配置优先**：环境变量 > 动态计算 > 硬编码默认值
3. **渐进降级**：重试时参数逐步降低，不直接跳到最低
4. **日志完整**：每次心跳、步骤进度、重试决策都有日志
5. **无副作用**：OCR 失败不污染主进程状态，临时文件正确清理
6. **测试覆盖**：核心逻辑（心跳检测、参数计算、重试策略）≥ 80% 覆盖率
