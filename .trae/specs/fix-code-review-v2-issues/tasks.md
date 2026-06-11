# Tasks

- [x] Task 1: 修复 pdf_generator.py NameError bug（最高优先级，运行时崩溃）
  - [x] SubTask 1.1: 修复 `_check_embedded_font_support` 方法中 `test_chars.get()` 结果未赋值的问题，将结果赋给 `test_char` 变量
  - [x] SubTask 1.2: 修复 `_check_font_support` 方法中同样的问题，将 `test_chars.get()` 结果赋给 `test_char` 变量
  - [x] SubTask 1.3: 验证修复后两个方法可正常运行

- [x] Task 2: 修复 ocr_worker.py 重复 logging 配置
  - [x] SubTask 2.1: 移除 `_ocr_worker_func` 中的 `logging.basicConfig()` 调用（第79-86行）
  - [x] SubTask 2.2: 保留 `_setup_subprocess_logger()` 作为唯一的日志配置方式
  - [x] SubTask 2.3: 验证子进程日志不再重复输出

- [x] Task 3: 移动 paddle_extractor.py typing import 到文件顶部
  - [x] SubTask 3.1: 将 `from typing import Optional, Dict, Any` 从第63行移动到文件顶部 import 区域
  - [x] SubTask 3.2: 删除原位置的 typing import 行

- [x] Task 4: 移除 pdf_generator.py 日志中的 emoji
  - [x] SubTask 4.1: 替换 `✅` 为纯文本标记如 `[OK]`
  - [x] SubTask 4.2: 替换 `⚠️` 为纯文本标记如 `[WARN]`
  - [x] SubTask 4.3: 替换 `❌` 为纯文本标记如 `[FAIL]`

- [x] Task 5: 统一 paddle_extractor.py 字体大小估算逻辑
  - [x] SubTask 5.1: 将 `_process_page_layout` 中第784-826行的内联字体估算代码替换为调用 `_estimate_font_size_from_textlines`
  - [x] SubTask 5.2: 验证其他三处估算调用（第866-869行、第907-910行、第951-955行）已使用统一方法

- [x] Task 6: 封装 paddle_extractor.py logger 恢复逻辑
  - [x] SubTask 6.1: 将 `_create_pipeline` 中第256-343行的 logger 恢复代码提取为 `_restore_logger_state(root_level_before, root_handlers_before)` 方法
  - [x] SubTask 6.2: 在 `_create_pipeline` 中调用新方法

- [x] Task 7: 添加 ocr_worker.py 环境变量安全性注释
  - [x] SubTask 7.1: 在 `_ocr_worker_func` 的 os.environ 设置块前添加注释，说明仅在 spawn 子进程中安全

- [x] Task 8: 调整 config.py OCR_MAX_TOTAL_TIME 默认值为 252000（70小时）
  - [x] SubTask 8.1: 将 `config.py` 中 `OCR_MAX_TOTAL_TIME` 默认值从 `86400` 改为 `252000`
  - [x] SubTask 8.2: 验证 2000 页文档（medium 分级）动态计算值 240300 秒不被 cap 截断

# Task Dependencies
- Task 1 无依赖，最高优先级
- Task 2-8 相互独立，可并行执行
- Task 5 依赖 Task 3（typing import 位置）
