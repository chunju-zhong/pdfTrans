# FONT_DEBUG 日志缺失问题深度分析 Spec

## Why
OCR 子进程中 `[FONT_DEBUG]` 日志（位于 `paddle_extractor.py:412`）从未出现在 `app.log` 中，导致无法调试字体大小估算问题。需要深度分析根因并修复。

## What Changes
- 修复 OCR 子进程中 `modules.ocr.paddle_extractor` logger 的日志丢失问题
- **BREAKING**: 无破坏性变更，仅修复日志可见性

## Impact
- Affected specs: 无
- Affected code: `modules/ocr/ocr_worker.py`, `modules/ocr/paddle_extractor.py`

## 深度分析：根因

### 调用链

```
app.py → setup_logging() → logging.basicConfig(level=INFO, handlers=[FileHandler('app.log'), StreamHandler])
  → translation_service → pdf_extractor.extract() → run_ocr_in_subprocess()
    → multiprocessing.Process(target=_ocr_worker_func, context='spawn')
      → _ocr_worker_func()
        → logging.basicConfig(level=INFO, handlers=[FileHandler('app.log'), StreamHandler])
        → PaddleOcrExtractor.extract_from_pdf()
          → _create_pipeline() → PPStructureV3(...)  ← 关键点
          → _process_page_layout() → logger.info("[FONT_DEBUG]...")  ← 从未出现
```

### 日志证据

`app.log` 中 `paddle_extractor` 的日志在以下位置**中断**：

```
08:37:02 - 创建PP-StructureV3管线: lang=en, device=cpu, use_table=False, use_formula=False
08:37:06 - 创建管线前(use_table=False, use_formula=False): 内存使用 304 MB
                          ← 此后 paddle_extractor 的所有日志消失
08:46:36 - translation_service - PDF文本提取完成  ← 10分钟后才有后续日志
```

**FONT_DEBUG 日志从未出现，"步骤1管线创建"内存日志也未出现，"步骤1完成"也未出现。**

### 根因：PPStructureV3 构造破坏了子进程的 logger handlers

**问题出在 `_create_pipeline()` 方法中 `PPStructureV3(...)` 的构造过程。**

1. **子进程 spawn 模式**：`multiprocessing.get_context('spawn')` 创建的子进程不继承父进程的 logging 配置。`ocr_worker.py:44-52` 在子进程开头调用了 `logging.basicConfig()` 配置了 root logger 的 handlers。

2. **PPStructureV3 构造破坏 handlers**：代码中已有防护逻辑（`paddle_extractor.py:195-227`），检测 PPStructureV3 构造后 root logger handlers 是否减少。但这个防护逻辑**存在致命缺陷**：

   **缺陷 1：只恢复 root logger，不恢复子 logger**
   - `modules.ocr.paddle_extractor` 的 logger 是 `logging.getLogger('modules.ocr.paddle_extractor')`，这是一个子 logger
   - Python logging 的传播机制：子 logger 的日志会向上传播到 root logger
   - 但如果 PPStructureV3 构造过程中**修改了 root logger 的 level 或清除了 handlers**，子 logger 的日志即使传播到 root 也会被丢弃
   - 防护代码只检查了 handler 数量，**没有检查 root logger 的 level 是否被修改**

   **缺陷 2：PPStructureV3 可能不只是移除 handlers，还可能修改 root logger 的 level**
   - PaddleX/PaddleOCR 内部可能将 root logger 的 level 设置为 `WARNING` 或更高
   - 这样 `INFO` 级别的 `[FONT_DEBUG]` 日志就会被 root logger 的 level 过滤掉
   - 防护代码完全没有检查和恢复 root logger 的 level

   **缺陷 3：PPStructureV3 可能添加了 NullHandler 或修改了 propagate**
   - PaddleOCR 内部可能给 root logger 添加了 `NullHandler`，或者修改了子 logger 的 `propagate=False`
   - 这会导致日志不再传播到有效的 handler

3. **时间线分析**：
   - `08:37:06` - "创建管线前" 日志出现（在 `PPStructureV3(...)` 调用之前）
   - `PPStructureV3(...)` 构造耗时约 5 秒（从 08:37:06 到约 08:37:11）
   - 构造完成后，`_log_memory("步骤1管线创建")` 和 `logger.info("[FONT_DEBUG]...")` 都**没有出现**
   - 这证明问题发生在 `PPStructureV3(...)` 构造过程中，而不是在后续的页面处理中

4. **子进程日志写入的是同一个 app.log**：子进程的 `basicConfig` 配置了 `FileHandler('app.log')`，但 PPStructureV3 构造后可能：
   - 关闭了 FileHandler
   - 修改了 root logger level
   - 添加了新的 handler 指向其他文件

### 为什么翻译最终成功了？

OCR 子进程最终**确实完成了**（08:46:36 翻译服务收到提取结果），说明 `extract_from_pdf()` 正常执行完毕，只是**日志被静默丢弃了**。这进一步证实是 logger handler/level 被破坏，而非进程崩溃。

## ADDED Requirements

### Requirement: 子进程日志完整性保障
系统 SHALL 确保 OCR 子进程中所有 logger 的日志（包括 `modules.ocr.paddle_extractor` 的 INFO 级别日志）在 PPStructureV3 构造前后均能正常输出到 `app.log` 和 stderr。

#### Scenario: PPStructureV3 构造后 FONT_DEBUG 日志正常输出
- **WHEN** OCR 子进程执行 `_create_pipeline()` 构造 PPStructureV3
- **AND** `_process_page_layout()` 中执行 `logger.info("[FONT_DEBUG]...")`
- **THEN** 该日志 SHALL 出现在 `app.log` 中

#### Scenario: PPStructureV3 构造修改了 root logger
- **WHEN** PPStructureV3 构造过程修改了 root logger 的 level 或 handlers
- **THEN** 系统 SHALL 在构造后恢复 root logger 的 level 为 INFO
- **AND** 系统 SHALL 恢复 root logger 的 handlers 为 FileHandler('app.log') + StreamHandler

#### Scenario: PPStructureV3 构造修改了子 logger 的 propagate
- **WHEN** PPStructureV3 构造过程将某个 logger 的 propagate 设置为 False
- **THEN** 系统 SHALL 恢复该 logger 的 propagate 为 True

## MODIFIED Requirements

### Requirement: _create_pipeline 日志防护增强
`_create_pipeline()` 方法中的 PPStructureV3 构造后日志防护逻辑 SHALL 从仅检查 handler 数量增强为：
1. 检查并恢复 root logger 的 level（确保为 INFO 或更低）
2. 检查并恢复 root logger 的 handlers（确保 FileHandler + StreamHandler 存在）
3. 检查并恢复 `modules.ocr.paddle_extractor` logger 的 propagate 属性（确保为 True）
4. 检查 `modules.ocr.paddle_extractor` logger 自身的 level 和 handlers

## REMOVED Requirements
无
