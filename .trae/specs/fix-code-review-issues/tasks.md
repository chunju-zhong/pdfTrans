# Tasks

## 阶段1：安全问题修复（CRITICAL + HIGH）— 使用 security-review 技能

- [x] Task 1: 修复下载路由安全性（发现 #1）
  - [x] SubTask 1.1: 在 `app.py` 的 `download_file` 路由中添加文件名校验
  - [x] SubTask 1.2: 拒绝包含路径分隔符或 `..` 的文件名，返回 400 错误

- [x] Task 2: 修复安全配置默认值（发现 #2, #3）
  - [x] SubTask 2.1: 移除 `config.py` 中 SECRET_KEY 的硬编码回退值，改为缺少时抛出 RuntimeError
  - [x] SubTask 2.2: 将 `config.py` 中 DEBUG 默认值从 'True' 改为 'False'
  - [x] SubTask 2.3: 将 `app.py` 中 app.run 的 host 从 '0.0.0.0' 改为 '127.0.0.1'

- [x] Task 3: 修复输入长度限制（发现 #14）
  - [x] SubTask 3.1: 在 `parse_page_range` 中添加输入长度限制（最大 1000 字符）

## 阶段2：数据完整性修复（MEDIUM）— 使用 python-patterns 技能

- [x] Task 4: 修复翻译失败静默丢数据（发现 #10）
  - [x] SubTask 4.1: 在 `process_merged_blocks` 中，翻译失败时回退到原文
  - [x] SubTask 4.2: 在 `process_original_blocks` 中同样回退到原文
  - [x] SubTask 4.3: 在 `_process_table_translation` 中同样回退到原文

- [x] Task 5: 修复字体大小回退算法（发现 #8）
  - [x] SubTask 5.1: 基于典型行高 12pt 估算行数

- [x] Task 6: 修复 PDF 生成器页码范围忽略（发现 #9）
  - [x] SubTask 6.1: 在 `generate_pdf` 方法签名中添加 `target_pages=None` 参数
  - [x] SubTask 6.2: 当 `target_pages` 有值时，仅输出指定页面
  - [x] SubTask 6.3: 在调用链中传递页码范围

## 阶段3：资源管理与健壮性修复（MEDIUM + LOW）— 使用 python-patterns 技能

- [x] Task 7: 修复 OCR 子进程健壮性（发现 #4, #5, #6）
  - [x] SubTask 7.1: 强制 `use_gpu=False`
  - [x] SubTask 7.2: 用 `result_queue.get(timeout=5)` 替代 `get_nowait()`
  - [x] SubTask 7.3: 为 `modules.ocr.ocr_worker` logger 显式添加 handler

- [x] Task 8: 修复资源泄漏（发现 #7, #13, #15）
  - [x] SubTask 8.1: pdf_generator.py 用 try/finally 确保 new_doc 关闭
  - [x] SubTask 8.2: paddle_extractor.py 完成后清理临时图像目录
  - [x] SubTask 8.3: app.py get_pdf_pages 用 try/finally 确保临时文件删除

- [x] Task 9: 修复日志 handler 重复问题（发现 #12）
  - [x] SubTask 9.1: 保存原有 handler 引用后直接恢复

## 阶段4：验证 — 使用 verification-loop 技能

- [x] Task 10: 安全验证
  - [x] SubTask 10.1: 下载路由拒绝路径遍历文件名 ✓
  - [x] SubTask 10.2: SECRET_KEY 缺少时启动失败 ✓
  - [x] SubTask 10.3: DEBUG 默认为 False ✓
  - [x] SubTask 10.4: app.run 绑定 127.0.0.1 ✓

- [x] Task 11: 数据完整性验证
  - [x] SubTask 11.1: 翻译失败回退原文 ✓
  - [x] SubTask 11.2: 字体大小回退算法 120pt→10lines→9pt ✓
  - [x] SubTask 11.3: PDF 生成器支持 target_pages 参数 ✓

- [x] Task 12: 资源管理验证
  - [x] SubTask 12.1: OCR 子进程 use_gpu=False ✓
  - [x] SubTask 12.2: get(timeout=5) ✓
  - [x] SubTask 12.3: try/finally 关闭 new_doc ✓
  - [x] SubTask 12.4: 临时文件清理 ✓
  - [x] SubTask 12.5: 日志恢复不创建重复 handler ✓

- [x] Task 13: 回归测试
  - [x] SubTask 13.1: pytest 251 passed, 8 failed（失败为预先存在的 mock 问题）✓
  - [x] SubTask 13.2: 模块导入正常 ✓

# Task Dependencies
- Task 1, 2, 3 可并行（阶段1：安全问题）
- Task 4, 5, 6 可并行（阶段2：数据完整性）
- Task 7, 8, 9 可并行（阶段3：资源管理）
- Task 10-13 依赖前置 Task
