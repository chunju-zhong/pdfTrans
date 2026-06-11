# 修复 OCR 子进程日志丢失问题

## 问题摘要

OCR 子进程（spawn 模式）中，所有 `logger.info()` 日志（包括 `[FONT_DEBUG]`）不会写入 `app.log`，导致无法通过日志排查第1页丢失等关键问题。

## 根因分析

### 实验验证

通过 `test_ocr_logging2.py` 实测确认：

```
[CHILD] STEP1: root handlers=[], len=0
[CHILD] STEP2: after paddle_extractor import, root handlers=[], len=0
[CHILD] STEP3: after PPStructureV3 import, root handlers=[], len=0
[CHILD] NOT FOUND in app.log
```

**spawn 模式子进程的 root logger 始终没有 handler**。`_ocr_worker_func` 中没有调用 `setup_logging()` 或 `logging.basicConfig()`，所以子进程的所有 `logger.info()` 调用：
- 不会写入 `app.log`（没有 FileHandler）
- 仅通过 `logging.lastResort` 输出到 stderr（无格式化，可能被终端捕获但不在日志文件中）

### app.log 中前8行 paddle_extractor 日志的来源

这8行日志（L37-52）是通过 `logging.lastResort` 输出到 stderr，然后因 Flask 应用的启动方式（可能是终端重定向）间接出现在 app.log 中的。但 L52（`创建管线前`）之后，PPStructureV3 构造函数内部可能修改了 logging 状态，导致后续日志连 stderr 都不再输出。

### 两个独立问题

1. **子进程日志丢失**：`_ocr_worker_func` 没有配置 logging，导致所有日志静默丢弃
2. **PPStructureV3 构造后日志完全消失**：即使前8行日志通过 lastResort 输出到了 stderr，`PPStructureV3(...)` 构造后连 stderr 输出也停止了

## 修改计划

### 修改1：在子进程中配置 logging（核心修复）

**文件**: `modules/ocr/ocr_worker.py`

在 `_ocr_worker_func` 函数中，环境变量设置之后、导入 paddleocr 之前，添加 logging 配置：

```python
def _ocr_worker_func(pdf_path, pages, temp_images_dir, lang, use_gpu, result_queue):
    import os
    os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0.5'
    os.environ['CPU_NUM'] = '2'
    # ... 现有环境变量 ...

    # 子进程日志配置（spawn 模式不继承父进程 logging）
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),     # 追加到主进程的日志文件
            logging.StreamHandler()              # 同时输出到 stderr
        ]
    )

    try:
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        # ... 现有代码 ...
```

**为什么这样修改**：
- `FileHandler('app.log')` 使用相对路径，与主进程的 `logging_config.py` 一致
- `FileHandler` 默认以追加模式打开文件，不会覆盖主进程的日志
- 在导入 paddleocr 之前配置，确保所有后续日志都能写入 app.log

### 修改2：在 PPStructureV3 构造后恢复 logging handler（防御性修复）

**文件**: `modules/ocr/paddle_extractor.py`

在 `_create_pipeline` 方法中，`PPStructureV3(...)` 构造之后，添加日志恢复检查：

```python
def _create_pipeline(self, ...):
    # ... 现有代码到 L193 ...
    self._log_memory(f"创建管线前(use_table={use_table}, use_formula={use_formula})")

    # 记录当前 root logger handlers
    root_logger = logging.getLogger()
    handler_count_before = len(root_logger.handlers)

    pipeline = PPStructureV3(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        use_table_recognition=use_table,
        use_formula_recognition=use_formula,
        use_region_detection=use_region_detection,
        device=device,
        lang=self.lang,
    )

    # PPStructureV3 构造可能通过 PaddleX import_guard 破坏 root logger handlers
    handler_count_after = len(root_logger.handlers)
    if handler_count_after < handler_count_before:
        logger.warning(f"PPStructureV3 构造移除了 root logger handlers "
                       f"({handler_count_before} -> {handler_count_after})，正在恢复")
        # 重新添加 FileHandler
        has_file_handler = any(isinstance(h, logging.FileHandler) for h in root_logger.handlers)
        if not has_file_handler:
            root_logger.addHandler(logging.FileHandler('app.log'))
        has_stream_handler = any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
                                  for h in root_logger.handlers)
        if not has_stream_handler:
            root_logger.addHandler(logging.StreamHandler())

    return pipeline
```

### 修改3：FONT_DEBUG 日志增加 label 和 is_body_text 信息

**文件**: `modules/ocr/paddle_extractor.py`

在 `_process_page_layout` 的 FONT_DEBUG 日志中增加关键字段，方便排查第1页丢失问题：

```python
# L386-387 替换为：
logger.info(f"[FONT_DEBUG] page={page_num}, label={label}, is_body={label not in self.NON_BODY_LABELS}, "
            f"text={repr(text[:30])}, font_size={estimated_font_size:.2f}")
```

移除 `print()` 行（子进程的 print 输出不可靠）。

## 清理

删除测试文件：
- `test_logging_subprocess.py`
- `test_ocr_logging.py`
- `test_ocr_logging2.py`
- `test_child.log`

## 验证步骤

1. 重新运行 OCR 翻译任务
2. 检查 app.log 中是否出现 `[FONT_DEBUG]` 日志
3. 检查 app.log 中是否出现 `步骤1管线创建`、`步骤1完成` 等之前丢失的日志
4. 通过 FONT_DEBUG 的 `label` 和 `is_body` 字段确认第1页的块被识别为什么标签
5. 确认 `is_body_text` 过滤是否是第1页丢失的直接原因
