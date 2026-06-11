# Blueprint: OCR 内存优化 — 保留表格和公式识别

## 目标

在 minimal 内存级别（<8GB 可用内存）的机器上，保留表格和公式识别功能的同时，优化内存使用，避免因内存交换（swapping）导致心跳中断和进程被杀。降级策略也不跳过表格和公式识别，改为更温和的降级方式。

## 根因

270 秒心跳中断的直接原因：公式识别管线在 minimal 级别机器上触发内存交换，整个子进程被操作系统冻结，心跳线程无法执行。

内存链路：

1. 步骤1完成后，`all_layout_results` + `text_blocks_by_page` + `page_images` 仍占用 \~300-500MB
2. 步骤2（表格识别）完成后，虽然管线已释放，但数据仍在内存
3. 步骤3创建公式管线时，PaddleOCR 加载模型需要 \~500-700MB
4. 在 <8GB 可用内存的机器上，总内存需求超过物理内存 → swapping → 进程冻结 → 心跳中断

***

## Step 1: 增大 minimal 级别的心跳超时

**文件**: `modules/ocr/system_profiler.py`
**依赖**: 无

### 上下文

minimal 级别的心跳超时为 240 秒（`base_per_page=120, heartbeat_timeout=max(90, 120*2)=240`），但 swapping 可能冻结进程 5-10 分钟。增大心跳超时可以容忍短暂的 swapping，避免误杀正在恢复的进程。

### 任务

1. 在 `compute_timeout_params` 中，为 minimal 级别设置更大的心跳超时：

   * 当前：`heartbeat_timeout = max(90, base_per_page * 2)` → minimal 得到 240 秒

   * 修改为按 tier 设置心跳超时倍数：

     ```python
     tier_heartbeat_multiplier = {
         "minimal": 3,
         "low": 2,
         "medium": 2,
         "high": 2,
         "unlimited": 2,
     }
     heartbeat_timeout = max(90, base_per_page * tier_heartbeat_multiplier[self.tier])
     ```

   * minimal: `max(90, 120*3) = 360` 秒

   * 其他级别保持不变

### 验证

* minimal 级别的 `heartbeat_timeout` 为 360 秒

### 退出条件

minimal 级别心跳超时从 240 秒增大到 360 秒

***

## Step 2: 降级策略改为不跳过表格和公式，增加更温和的降级手段

**文件**: `modules/ocr/ocr_worker.py`
**依赖**: 无

### 上下文

当前 `_degrade_params` 在重试时跳过表格（attempt >= 1）和公式（attempt >= 2）识别。用户要求保留表格和公式识别，因此需要移除跳过逻辑，改为更温和的降级方式：

**替代降级手段**：

1. 进一步降低 DPI（每次重试多降 20，当前已降 20）
2. 进一步减少内存上限（每次重试多乘 0.7，当前已乘 0.8）
3. 进一步减少线程数（当前已减 1，可多减 1）
4. 增加超时预算（当前已乘 1.5，可增大到 2.0）

### 任务

1. 移除 `_degrade_params` 中的 `skip_table` 和 `skip_formula` 逻辑（删除 `if attempt >= 1` 和 `if attempt >= 2` 两个分支）
2. 增强现有降级手段：

   * DPI 降级：从 `current_dpi - 20` 改为 `current_dpi - 30`（每次多降 10）

   * 内存上限降级：从 `* 0.8` 改为 `* 0.7`（更积极地释放内存）

   * 线程数降级：从 `max(1, current - 1)` 改为 `max(1, current - attempt)`（重试越多减越多）

   * 超时预算：从 `* 1.5` 改为 `* 2.0`（给更多时间）
3. 更新日志格式，移除"跳过表格/公式"字段

### 验证

* 降级后 `skip_table` 和 `skip_formula` 不再被设置为 `True`

* DPI、内存上限、线程数的降级更激进

### 退出条件

降级策略不再跳过表格和公式识别，改为更温和的参数降级

***

## Step 3: 步骤间精简布局数据 + 公式逐页管线 + 内存检查

**文件**: `modules/ocr/paddle_extractor.py`
**依赖**: Step 1, Step 2（先完成独立文件的修改）

### 上下文

三个子任务都修改 `paddle_extractor.py`，必须串行实施，避免合并冲突。

#### 3a: 精简布局数据

`all_layout_results` 在步骤1完成后持有所有页面的完整布局数据，但步骤2和步骤3只需要部分字段。精简数据可释放数百 MB。

**必须保留的字段**（步骤2/3/4都需要）：

* `has_table` — 步骤2判断是否需要表格识别

* `has_formula` — 步骤3判断是否需要公式识别

* `image_regions` — 步骤4图表裁剪需要

* `layout_bboxes` — 步骤2表格定位需要

* `pixel_bbox` — 步骤4图像裁剪坐标需要（**关键**：不能删除，否则图像裁剪会静默失败）

**可以删除的字段**：

* `text_blocks` — 已转移到 `text_blocks_by_page`

#### 3b: 公式识别逐页创建/销毁管线

当前公式识别是一次创建管线处理所有含公式页面。逐页创建/销毁管线将内存峰值从"管线+所有页面图像"降为"管线+单页图像"。

**逐页模式判断**：在步骤3开始前检查可用内存。如果可用内存 < 3GB，使用逐页模式。这比依赖 tier 更准确，因为内存状态是动态的。

#### 3c: 步骤3开始前主动检查可用内存

即使启用了公式识别，如果可用内存不足以加载公式管线（<1.5GB），应该主动跳过。这是最后的安全网——只有在极端低内存时才跳过，而非降级时跳过。

### 任务

#### 3a: 精简布局数据

1. 在步骤1完成后（`del layout_pipeline; gc.collect()` 之后），遍历 `all_layout_results`，只保留必要字段：

   * `has_table`, `has_formula`, `image_regions`, `layout_bboxes`, `pixel_bbox`
2. 删除每页结果中的 `text_blocks`（已转移到 `text_blocks_by_page`）
3. 调用 `gc.collect()`
4. 记录精简前后的内存变化日志

#### 3b: 公式逐页管线

1. 在步骤3公式识别循环中，在创建管线前检查可用内存：

   * 可用内存 < 3GB：逐页创建/销毁管线模式

   * 可用内存 >= 3GB：保持当前行为（一次创建管线处理所有页面）
2. 逐页模式：每页创建管线 → predict → 销毁管线 → gc.collect()
3. 每页处理后显式 `del img_array`
4. 添加日志记录逐页模式

#### 3c: 内存检查

1. 在步骤3开始前（`if formula_pages:` 之后），调用 `_check_available_memory()` 检查可用内存
2. 如果可用内存 < 1.5GB（`1.5 * 1024 * 1024 * 1024`），记录警告并跳过公式识别
3. 添加日志记录内存检查结果

### 验证

* 日志中出现 "精简布局数据" 相关信息

* 低内存环境下日志中出现 "逐页创建公式管线" 或 "可用内存不足，跳过公式识别" 信息

### 退出条件

* 步骤2开始前，`all_layout_results` 中每页只包含必要字段

* 低内存时公式识别使用逐页管线模式

* 可用内存 <1.5GB 时优雅跳过公式识别（仅此极端情况才跳过）

***

## 实施顺序

```
Step 1 (心跳超时 - system_profiler.py) ──┐
Step 2 (降级策略 - ocr_worker.py)     ──┼── 可并行
                                          │
Step 3 (paddle_extractor.py)          ──┘── 串行，依赖 Step 1/2 完成
  ├─ 3a: 精简布局数据
  ├─ 3b: 公式逐页管线
  └─ 3c: 内存检查
```

## 回滚策略

每个 Step 独立，可单独回滚：

* Step 1: 恢复 `heartbeat_timeout = max(90, base_per_page * 2)`

* Step 2: 恢复 `skip_table`/`skip_formula` 逻辑和原始降级参数

* Step 3a: 恢复 `all_layout_results` 的完整数据

* Step 3b: 恢复为一次创建管线

* Step 3c: 移除内存检查

