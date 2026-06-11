# OCR 默认打开公式识别功能

## 目标
将 OCR 公式识别功能改为默认启用，即使在低内存环境下也不自动跳过。

## 当前行为分析

公式识别是否跳过由以下决策链决定：

1. **`system_profiler.py:159-160`** — `should_skip_formula()` 在 `minimal` 内存分级（可用内存 < 8GB）时返回 `True`，跳过公式识别
2. **`ocr_worker.py:99`** — 从 `ocr_params` 读取 `skip_formula`，传入 `PaddleOcrExtractor`
3. **`paddle_extractor.py:107`** — `self._skip_formula` 优先使用传入参数，否则用 `config.OCR_SKIP_FORMULA`
4. **`config.py:92`** — `OCR_SKIP_FORMULA` 默认 `false`（不跳过），但被 `system_profiler` 覆盖

**问题**：`system_profiler.should_skip_formula()` 在 `minimal` 分级时强制跳过公式识别，覆盖了 `config.OCR_SKIP_FORMULA = false` 的默认设置。

## 实施步骤

### Step 1: 修改 `system_profiler.py` 的 `should_skip_formula` 方法
- 将 `should_skip_formula()` 改为始终返回 `False`，即默认不跳过公式识别
- 保留 `config.OCR_SKIP_FORMULA` 作为用户手动跳过的配置入口

**文件**: `modules/ocr/system_profiler.py`
**修改**: 第 159-160 行
```python
# 当前:
def should_skip_formula(self):
    return self.tier == "minimal"

# 改为:
def should_skip_formula(self):
    return False
```

### Step 2: 验证 `paddle_extractor.py` 中 `config.OCR_SKIP_FORMULA` 仍生效
- 确认 `paddle_extractor.py:107` 的逻辑：当 `skip_formula` 参数未传入时，使用 `config.OCR_SKIP_FORMULA`
- 这意味着用户仍可通过设置 `OCR_SKIP_FORMULA=true` 环境变量手动跳过公式识别
- 无需修改此文件

### Step 3: 更新 `system_profiler.py` 的日志输出
- `compute_all_params` 中的日志已包含 `skip_formula=%s`，修改后会自动显示 `False`
- 无需额外修改

## 影响范围
- `modules/ocr/system_profiler.py` — 修改 `should_skip_formula` 方法
- 低内存环境（<8GB 可用内存）的机器将默认启用公式识别，可能增加内存使用
- 用户仍可通过 `OCR_SKIP_FORMULA=true` 环境变量手动跳过

## 风险评估
- **低风险**：公式识别只在检测到页面含公式时才执行（`has_formula` 过滤），不会对所有页面都运行
- **内存风险**：`minimal` 分级机器内存较少，启用公式识别可能增加内存压力，但有 `memory_cap_formula` 限制
- **降级保护**：OCR 重试机制在第 2 次重试时会自动跳过公式识别（`ocr_worker.py:154`），作为安全网
