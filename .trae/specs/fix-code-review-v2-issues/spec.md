# Code Review V2 修复计划 Spec

## Why
最新一轮 code review（feat/ocr-extraction vs develop）发现 1 个 CRITICAL、6 个 HIGH、7 个 MEDIUM、3 个 LOW 级别问题，其中包含运行时崩溃 bug（NameError）和重复 logging 配置等必须修复的问题。

## What Changes
- 修复 pdf_generator.py 中 `_check_embedded_font_support` 和 `_check_font_support` 的 NameError bug（`test_char` 未定义）
- 修复 ocr_worker.py 子进程函数中重复 logging 配置
- 移动 paddle_extractor.py 的 typing import 到文件顶部
- 移除 pdf_generator.py 日志中的 emoji
- 统一 paddle_extractor.py 中重复的字体大小估算逻辑
- 封装 paddle_extractor.py 中 logger 恢复逻辑为独立方法
- 添加 ocr_worker.py 环境变量设置的安全性注释
- 调整 config.py OCR_MAX_TOTAL_TIME 默认值为 252000（70小时），以支持 2000+ 页文档的完整处理

**注意**：paddle_extractor.py（1485行）和 translation_service.py（1897行）的超长文件拆分属于架构重构，不在本次修复范围内，建议作为独立 spec 后续处理。

## Impact
- Affected code: `modules/pdf_generator.py`, `modules/ocr/ocr_worker.py`, `modules/ocr/paddle_extractor.py`, `config.py`

## ADDED Requirements

### Requirement: 修复 pdf_generator.py 字体检测 NameError bug
`_check_embedded_font_support` 和 `_check_font_support` 方法 SHALL 正确使用 `test_chars` 字典变量，修复 `test_char` 未定义导致的 NameError。

#### Scenario: 检查字体是否支持中文
- **WHEN** 调用 `_check_font_support(font_path, 'zh')`
- **THEN** SHALL 从 `test_chars` 字典获取 `'你好世界'` 测试字符并逐字检查，不抛出 NameError

#### Scenario: 检查内嵌字体是否支持目标语言
- **WHEN** 调用 `_check_embedded_font_support(page, fontname, 'zh')`
- **THEN** SHALL 正确获取测试字符并检测，不抛出 NameError

### Requirement: 修复 ocr_worker.py 子进程重复 logging 配置
`_ocr_worker_func` 函数 SHALL 仅使用 `_setup_subprocess_logger()` 配置日志，移除冗余的 `logging.basicConfig()` 调用，避免日志重复输出。

#### Scenario: 子进程日志不重复
- **WHEN** OCR 子进程运行时
- **THEN** 每条日志 SHALL 仅输出一次，不出现重复

### Requirement: 移动 typing import 到文件顶部
`paddle_extractor.py` 中的 `from typing import Optional, Dict, Any` SHALL 移动到文件顶部与其他标准库导入一起。

### Requirement: 移除日志中的 emoji
`pdf_generator.py` 中的日志 SHALL 不包含 emoji 字符（如 ✅、⚠️、❌），确保日志可读性和可搜索性。

### Requirement: 统一字体大小估算逻辑
`paddle_extractor.py` 中多处重复的字体大小估算代码 SHALL 统一使用 `_estimate_font_size_from_textlines` 静态方法，消除代码重复。

### Requirement: 封装 logger 恢复逻辑
`_create_pipeline` 中的 logger 恢复代码 SHALL 封装为 `_restore_logger_state` 方法，降低 `_create_pipeline` 的复杂度。

### Requirement: 添加子进程环境变量安全性注释
`_ocr_worker_func` 中的 `os.environ` 设置 SHALL 添加注释说明仅在 spawn 子进程中安全使用，若改为线程模式会污染主进程。

### Requirement: 调整 OCR_MAX_TOTAL_TIME 默认值为 70 小时
`config.py` 中 `OCR_MAX_TOTAL_TIME` 的默认值 SHALL 从 86400（24小时）调整为 252000（70小时），以支持 2000+ 页文档的完整处理。当前动态超时机制：
- `system_profiler.py` 的 `compute_timeout_params(page_count)` 根据内存分级和页数动态计算 `max_total_time`，公式为 `max(600, base_per_page * page_count * 2 + 300)`
- `ocr_worker.py` 用 `min(dynamic_max_total_time, config_max_total_time)` 将动态值限制在配置上限内

示例计算（medium 分级，base_per_page=60）：
- 10 页：1500秒（25分钟），不触发 cap
- 100 页：12300秒（3.4小时），不触发 cap
- 2000 页：240300秒（66.7小时），旧 cap 86400 会截断，新 cap 252000 不截断

## MODIFIED Requirements
无

## REMOVED Requirements
无
